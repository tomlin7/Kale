const std = @import("std");
const ast = @import("ast.zig");
const types = @import("types.zig");
const Type = types.Type;
const TypeContext = types.TypeContext;
const lexer_mod = @import("lexer.zig");
const parser_mod = @import("parser.zig");

pub const SymbolKind = enum {
    variable,
    function,
    struct_sym,
    enum_sym,
    module_alias,
};

pub const Symbol = struct {
    kind: SymbolKind,
    name: []const u8,
    type: *Type,
    mangled_name: []const u8,
    is_extern: bool = false,
    is_varargs: bool = false,
    module: ?*Module = null,
};

pub const Scope = struct {
    allocator: std.mem.Allocator,
    parent: ?*Scope = null,
    symbols: std.StringHashMap(*Symbol),

    pub fn init(allocator: std.mem.Allocator, parent: ?*Scope) Scope {
        return .{
            .allocator = allocator,
            .parent = parent,
            .symbols = std.StringHashMap(*Symbol).init(allocator),
        };
    }

    pub fn lookup(self: *const Scope, name: []const u8) ?*Symbol {
        if (self.symbols.get(name)) |sym| return sym;
        if (self.parent) |p| return p.lookup(name);
        return null;
    }

    pub fn define(self: *Scope, name: []const u8, sym: *Symbol) !void {
        try self.symbols.put(name, sym);
    }
};

pub const Module = struct {
    name: []const u8,
    path: []const u8,
    program: ast.Program,
    scope: *Scope,
};

pub const Checker = struct {
    allocator: std.mem.Allocator,
    type_ctx: TypeContext,
    modules: std.StringHashMap(*Module),
    current_module: ?*Module = null,
    current_scope: *Scope,
    search_paths: std.ArrayList([]const u8),
    errors: usize = 0,

    pub fn init(allocator: std.mem.Allocator) !Checker {
        const type_ctx = try TypeContext.init(allocator);
        const root_scope = try allocator.create(Scope);
        root_scope.* = Scope.init(allocator, null);

        var search_paths: std.ArrayList([]const u8) = .{};
        try search_paths.append(allocator, ".");
        try search_paths.append(allocator, "packages/std");
        try search_paths.append(allocator, "packages");
        try search_paths.append(allocator, "libs");

        return .{
            .allocator = allocator,
            .type_ctx = type_ctx,
            .modules = std.StringHashMap(*Module).init(allocator),
            .current_module = null,
            .current_scope = root_scope,
            .search_paths = search_paths,
            .errors = 0,
        };
    }

    pub fn addSearchPath(self: *Checker, path: []const u8) !void {
        try self.search_paths.append(self.allocator, path);
    }

    pub fn resolveType(self: *Checker, type_ref: ast.TypeRef) !*Type {
        var base_type: *Type = undefined;

        if (std.mem.eql(u8, type_ref.name, "int")) {
            base_type = self.type_ctx.type_int;
        } else if (std.mem.eql(u8, type_ref.name, "int32") or std.mem.eql(u8, type_ref.name, "i32")) {
            base_type = self.type_ctx.type_int32;
        } else if (std.mem.eql(u8, type_ref.name, "float") or std.mem.eql(u8, type_ref.name, "float32") or std.mem.eql(u8, type_ref.name, "f32")) {
            base_type = self.type_ctx.type_float;
        } else if (std.mem.eql(u8, type_ref.name, "double") or std.mem.eql(u8, type_ref.name, "float64") or std.mem.eql(u8, type_ref.name, "f64")) {
            base_type = self.type_ctx.type_double;
        } else if (std.mem.eql(u8, type_ref.name, "string")) {
            base_type = self.type_ctx.type_string;
        } else if (std.mem.eql(u8, type_ref.name, "bool")) {
            base_type = self.type_ctx.type_bool;
        } else if (std.mem.eql(u8, type_ref.name, "char")) {
            base_type = self.type_ctx.type_char;
        } else if (std.mem.eql(u8, type_ref.name, "void")) {
            base_type = self.type_ctx.type_void;
        } else if (std.mem.indexOfScalar(u8, type_ref.name, '.')) |dot_idx| {
            // Qualified type: mod.StructName
            const mod_alias = type_ref.name[0..dot_idx];
            const struct_name = type_ref.name[dot_idx + 1 ..];
            if (self.current_scope.lookup(mod_alias)) |mod_sym| {
                if (mod_sym.module) |m| {
                    if (m.scope.lookup(struct_name)) |st_sym| {
                        base_type = st_sym.type;
                    } else {
                        base_type = self.type_ctx.type_unknown;
                    }
                } else {
                    base_type = self.type_ctx.type_unknown;
                }
            } else {
                base_type = self.type_ctx.type_unknown;
            }
        } else {
            // Custom struct or enum type
            if (self.current_scope.lookup(type_ref.name)) |sym| {
                base_type = sym.type;
            } else {
                // Forward-declare struct type if not yet fully defined
                const st = try self.allocator.create(Type);
                st.* = Type{
                    .kind = .struct_type,
                    .data = .{
                        .struct_type = .{
                            .name = type_ref.name,
                            .fields = &.{},
                        },
                    },
                };
                const sym = try self.allocator.create(Symbol);
                sym.* = Symbol{
                    .kind = .struct_sym,
                    .name = type_ref.name,
                    .type = st,
                    .mangled_name = type_ref.name,
                };
                try self.current_scope.define(type_ref.name, sym);
                base_type = st;
            }
        }

        var res = base_type;
        var i: usize = 0;
        while (i < type_ref.ptr_depth) : (i += 1) {
            res = try self.type_ctx.getPointerTo(res);
        }

        if (type_ref.is_array) {
            res = try self.type_ctx.getArrayOf(res, type_ref.array_size);
        }

        return res;
    }

    pub fn loadModule(self: *Checker, file_path: []const u8) anyerror!*Module {
        // Check if already loaded
        var it = self.modules.iterator();
        while (it.next()) |entry| {
            if (std.mem.eql(u8, entry.value_ptr.*.path, file_path) or std.mem.eql(u8, entry.key_ptr.*, file_path)) {
                return entry.value_ptr.*;
            }
        }

        // Open and read file
        const file = std.fs.cwd().openFile(file_path, .{}) catch |err| {
            // Try searching search_paths
            var found_file: ?std.fs.File = null;
            var actual_path = file_path;
            for (self.search_paths.items) |sp| {
                const candidate = std.fs.path.join(self.allocator, &[_][]const u8{ sp, file_path }) catch continue;
                if (std.fs.cwd().openFile(candidate, .{})) |f| {
                    found_file = f;
                    actual_path = candidate;
                    break;
                } else |_| {}
            }
            if (found_file) |f| {
                return self.loadModuleFromFile(f, actual_path);
            }
            return err;
        };
        return self.loadModuleFromFile(file, file_path);
    }

    fn loadModuleFromFile(self: *Checker, file: std.fs.File, file_path: []const u8) !*Module {
        defer file.close();
        const src = try file.readToEndAlloc(self.allocator, 10 * 1024 * 1024);

        var lexer = lexer_mod.Lexer.init(self.allocator, src);
        const tokens = try lexer.tokenizeAll();

        var parser = parser_mod.Parser.init(self.allocator, tokens);
        const prog = try parser.parseProgram();

        var base_name = std.fs.path.basename(file_path);
        if (std.mem.endsWith(u8, base_name, ".kl")) {
            base_name = base_name[0 .. base_name.len - 3];
        }

        const mod_scope = try self.allocator.create(Scope);
        mod_scope.* = Scope.init(self.allocator, null);

        const mod = try self.allocator.create(Module);
        mod.* = Module{
            .name = base_name,
            .path = file_path,
            .program = prog,
            .scope = mod_scope,
        };
        try self.modules.put(file_path, mod);
        try self.modules.put(base_name, mod);

        // Bind this module
        const prev_mod = self.current_module;
        const prev_scope = self.current_scope;
        self.current_module = mod;
        self.current_scope = mod_scope;

        try self.checkModule(mod);

        self.current_module = prev_mod;
        self.current_scope = prev_scope;

        return mod;
    }

    pub fn checkModule(self: *Checker, mod: *Module) !void {
        // Pass 1: Register imports
        for (mod.program.statements) |stmt| {
            if (stmt.kind == .import_stmt) {
                const imp = stmt.data.import_stmt;
                const imported_mod = try self.loadModule(imp.path);
                const alias_name = imp.alias orelse imported_mod.name;

                const mod_sym = try self.allocator.create(Symbol);
                const mod_t = try self.allocator.create(Type);
                mod_t.* = Type{
                    .kind = .module,
                    .data = .{
                        .module = .{
                            .name = imported_mod.name,
                            .path = imported_mod.path,
                        },
                    },
                };
                mod_sym.* = Symbol{
                    .kind = .module_alias,
                    .name = alias_name,
                    .type = mod_t,
                    .mangled_name = alias_name,
                    .module = imported_mod,
                };
                try mod.scope.define(alias_name, mod_sym);
            } else if (stmt.kind == .from_import_stmt) {
                const fimp = stmt.data.from_import_stmt;
                const imported_mod = try self.loadModule(fimp.path);
                for (fimp.symbols) |item| {
                    if (imported_mod.scope.lookup(item.name)) |sym| {
                        const local_name = item.alias orelse item.name;
                        try mod.scope.define(local_name, sym);
                    }
                }
            }
        }

        // Pass 2: Register struct and enum declarations
        for (mod.program.statements) |stmt| {
            if (stmt.kind == .struct_decl) {
                const s = stmt.data.struct_decl;
                var fields: std.ArrayList(Type.StructField) = .{};
                for (s.fields) |f| {
                    const ft = try self.resolveType(f.type_ref);
                    try fields.append(self.allocator, .{ .name = f.name, .type = ft });
                }
                const st = try self.allocator.create(Type);
                st.* = Type{
                    .kind = .struct_type,
                    .data = .{
                        .struct_type = .{
                            .name = s.name,
                            .fields = try fields.toOwnedSlice(self.allocator),
                        },
                    },
                };
                const sym = try self.allocator.create(Symbol);
                sym.* = Symbol{
                    .kind = .struct_sym,
                    .name = s.name,
                    .type = st,
                    .mangled_name = s.name,
                };
                try mod.scope.define(s.name, sym);
            } else if (stmt.kind == .enum_decl) {
                const e = stmt.data.enum_decl;
                var members: std.ArrayList(Type.EnumMember) = .{};
                var next_val: i64 = 0;
                for (e.members) |m| {
                    const v = m.value orelse next_val;
                    next_val = v + 1;
                    try members.append(self.allocator, .{ .name = m.name, .value = v });
                }
                const et = try self.allocator.create(Type);
                et.* = Type{
                    .kind = .enum_type,
                    .data = .{
                        .enum_type = .{
                            .name = e.name,
                            .members = try members.toOwnedSlice(self.allocator),
                        },
                    },
                };
                const sym = try self.allocator.create(Symbol);
                sym.* = Symbol{
                    .kind = .enum_sym,
                    .name = e.name,
                    .type = et,
                    .mangled_name = e.name,
                };
                try mod.scope.define(e.name, sym);
            }
        }

        // Pass 3: Register function signatures (including externs)
        for (mod.program.statements) |stmt| {
            if (stmt.kind == .fn_decl) {
                const fn_d = stmt.data.fn_decl;
                const ret_t = try self.resolveType(fn_d.ret_type);
                var param_types: std.ArrayList(*Type) = .{};
                for (fn_d.params) |p| {
                    try param_types.append(self.allocator, try self.resolveType(p.type_ref));
                }

                const fn_t = try self.allocator.create(Type);
                fn_t.* = Type{
                    .kind = .function,
                    .data = .{
                        .function = .{
                            .param_types = try param_types.toOwnedSlice(self.allocator),
                            .ret_type = ret_t,
                        },
                    },
                };

                var mangled: []const u8 = fn_d.name;
                if (!fn_d.is_extern and !std.mem.eql(u8, fn_d.name, "main")) {
                    mangled = try std.fmt.allocPrint(self.allocator, "kale_{s}_{s}", .{ mod.name, fn_d.name });
                }

                const sym = try self.allocator.create(Symbol);
                sym.* = Symbol{
                    .kind = .function,
                    .name = fn_d.name,
                    .type = fn_t,
                    .mangled_name = mangled,
                    .is_extern = fn_d.is_extern,
                    .is_varargs = fn_d.is_varargs,
                    .module = mod,
                };
                try mod.scope.define(fn_d.name, sym);
            }
        }
    }
};
