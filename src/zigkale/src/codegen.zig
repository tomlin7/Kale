const std = @import("std");
const ast = @import("ast.zig");
const types = @import("types.zig");
const Type = types.Type;
const checker_mod = @import("checker.zig");
const Checker = checker_mod.Checker;
const Module = checker_mod.Module;
const Symbol = checker_mod.Symbol;
const TokenKind = @import("token.zig").TokenKind;

pub const Codegen = struct {
    allocator: std.mem.Allocator,
    checker: *Checker,
    root_module: *Module,
    out: std.ArrayList(u8),
    indent: usize = 0,

    pub fn init(allocator: std.mem.Allocator, checker: *Checker, root_module: *Module) Codegen {
        return .{
            .allocator = allocator,
            .checker = checker,
            .root_module = root_module,
            .out = .{},
            .indent = 0,
        };
    }

    fn writeIndent(self: *Codegen) !void {
        var i: usize = 0;
        while (i < self.indent) : (i += 1) {
            try self.out.appendSlice(self.allocator, "    ");
        }
    }

    fn writeLine(self: *Codegen, text: []const u8) !void {
        try self.writeIndent();
        try self.out.appendSlice(self.allocator, text);
        try self.out.append(self.allocator, '\n');
    }

    fn writeFmt(self: *Codegen, comptime fmt: []const u8, args: anytype) !void {
        const str = try std.fmt.allocPrint(self.allocator, fmt, args);
        try self.out.appendSlice(self.allocator, str);
    }

    fn writeLineFmt(self: *Codegen, comptime fmt: []const u8, args: anytype) !void {
        try self.writeIndent();
        try self.writeFmt(fmt, args);
        try self.out.append(self.allocator, '\n');
    }

    fn mapType(self: *Codegen, t: *const Type) anyerror![]const u8 {
        switch (t.kind) {
            .primitive => {
                return switch (t.data.primitive) {
                    .int_t => "int64_t",
                    .int32_t => "int32_t",
                    .float_t => "float",
                    .double_t => "double",
                    .bool_t => "bool",
                    .string_t => "const char*",
                    .char_t => "char",
                    .void_t => "void",
                };
            },
            .pointer => {
                const base = try self.mapType(t.data.pointer);
                return try std.fmt.allocPrint(self.allocator, "{s}*", .{base});
            },
            .array => {
                const elem = try self.mapType(t.data.array.elem_type);
                return try std.fmt.allocPrint(self.allocator, "{s}*", .{elem});
            },
            .struct_type => {
                return try std.fmt.allocPrint(self.allocator, "struct {s}", .{t.data.struct_type.name});
            },
            .enum_type => {
                return t.data.enum_type.name;
            },
            .function => {
                return "void*";
            },
            else => return "void*",
        }
    }

    fn mapTypeRef(self: *Codegen, tr: ast.TypeRef) anyerror![]const u8 {
        var base: []const u8 = "";
        if (std.mem.eql(u8, tr.name, "int")) {
            base = "int64_t";
        } else if (std.mem.eql(u8, tr.name, "int32") or std.mem.eql(u8, tr.name, "i32")) {
            base = "int32_t";
        } else if (std.mem.eql(u8, tr.name, "float") or std.mem.eql(u8, tr.name, "float32") or std.mem.eql(u8, tr.name, "f32")) {
            base = "float";
        } else if (std.mem.eql(u8, tr.name, "double") or std.mem.eql(u8, tr.name, "float64") or std.mem.eql(u8, tr.name, "f64")) {
            base = "double";
        } else if (std.mem.eql(u8, tr.name, "string")) {
            base = "const char*";
        } else if (std.mem.eql(u8, tr.name, "bool")) {
            base = "bool";
        } else if (std.mem.eql(u8, tr.name, "char")) {
            base = "char";
        } else if (std.mem.eql(u8, tr.name, "void")) {
            base = "void";
        } else if (std.mem.indexOfScalar(u8, tr.name, '.')) |dot_idx| {
            base = try std.fmt.allocPrint(self.allocator, "struct {s}", .{tr.name[dot_idx + 1 ..]});
        } else {
            // Check if struct or enum
            base = try std.fmt.allocPrint(self.allocator, "struct {s}", .{tr.name});
        }

        var res = base;
        var i: usize = 0;
        while (i < tr.ptr_depth) : (i += 1) {
            res = try std.fmt.allocPrint(self.allocator, "{s}*", .{res});
        }
        if (tr.is_array) {
            res = try std.fmt.allocPrint(self.allocator, "{s}*", .{res});
        }
        return res;
    }

    fn isStandardLibFunc(name: []const u8) bool {
        const std_funcs = [_][]const u8{
            "malloc", "free", "strlen", "strcmp", "strstr", "strncmp", "strcpy", "strncpy",
            "printf", "sprintf", "snprintf", "puts", "fopen", "fclose", "fseek", "ftell",
            "fread", "fwrite", "fputs", "fgets", "exit", "memcpy", "memmove", "memset", "memcmp",
            "pow", "sqrt", "sin", "cos", "tan", "floor", "ceil", "abs", "fabs",
            "system", "getenv", "atoi", "atof", "clock", "time",
        };
        for (std_funcs) |sf| {
            if (std.mem.eql(u8, name, sf)) return true;
        }
        return false;
    }

    pub fn generate(self: *Codegen) ![]const u8 {
        // Preamble
        try self.writeLine("#include <stdint.h>");
        try self.writeLine("#include <stdbool.h>");
        try self.writeLine("#include <stdio.h>");
        try self.writeLine("#include <stdlib.h>");
        try self.writeLine("#include <string.h>");
        try self.writeLine("#include <math.h>");
        try self.writeLine("");
        try self.writeLine("// --- Kale Runtime ---");
        try self.writeLine("static inline void _kale_print_int(int64_t x) { printf(\"%lld\", (long long)x); }");
        try self.writeLine("static inline void _kale_print_double(double x) { printf(\"%g\", x); }");
        try self.writeLine("static inline void _kale_print_bool(bool x) { printf(\"%s\", x ? \"true\" : \"false\"); }");
        try self.writeLine("static inline void _kale_print_str(const char* x) { if (x) printf(\"%s\", x); }");
        try self.writeLine("static inline void _kale_println(void) { printf(\"\\n\"); }");
        try self.writeLine("");

        // Collect all modules to emit (imported first, then root module)
        var all_modules: std.ArrayList(*Module) = .{};
        var mod_it = self.checker.modules.valueIterator();
        while (mod_it.next()) |m_ptr| {
            const m = m_ptr.*;
            if (m != self.root_module) {
                var already = false;
                for (all_modules.items) |existing| {
                    if (existing == m) {
                        already = true;
                        break;
                    }
                }
                if (!already) {
                    try all_modules.append(self.allocator, m);
                }
            }
        }
        try all_modules.append(self.allocator, self.root_module);

        // Forward declare all structs
        try self.writeLine("// --- Forward Struct Declarations ---");
        for (all_modules.items) |m| {
            for (m.program.statements) |stmt| {
                if (stmt.kind == .struct_decl) {
                    try self.writeLineFmt("struct {s};", .{stmt.data.struct_decl.name});
                }
            }
        }
        try self.writeLine("");

        // Emit all enums
        try self.writeLine("// --- Enum Definitions ---");
        for (all_modules.items) |m| {
            for (m.program.statements) |stmt| {
                if (stmt.kind == .enum_decl) {
                    const e = stmt.data.enum_decl;
                    try self.writeLineFmt("typedef enum {{", .{});
                    self.indent += 1;
                    var next_val: i64 = 0;
                    for (e.members, 0..) |mem, idx| {
                        const val = mem.value orelse next_val;
                        next_val = val + 1;
                        const comma = if (idx < e.members.len - 1) "," else "";
                        try self.writeLineFmt("{s}_{s} = {d}{s}", .{ e.name, mem.name, val, comma });
                    }
                    self.indent -= 1;
                    try self.writeLineFmt("}} {s};", .{e.name});
                    try self.writeLine("");
                }
            }
        }

        // Emit all struct definitions
        try self.writeLine("// --- Struct Definitions ---");
        for (all_modules.items) |m| {
            for (m.program.statements) |stmt| {
                if (stmt.kind == .struct_decl) {
                    const s = stmt.data.struct_decl;
                    try self.writeLineFmt("struct {s} {{", .{s.name});
                    self.indent += 1;
                    for (s.fields) |f| {
                        const ft_str = try self.mapTypeRef(f.type_ref);
                        try self.writeLineFmt("{s} {s};", .{ ft_str, f.name });
                    }
                    self.indent -= 1;
                    try self.writeLine("};");
                    try self.writeLine("");
                }
            }
        }

        // Function prototypes
        try self.writeLine("// --- Function Prototypes ---");
        for (all_modules.items) |m| {
            for (m.program.statements) |stmt| {
                if (stmt.kind == .fn_decl) {
                    const fn_d = stmt.data.fn_decl;
                    if (fn_d.is_extern) {
                        if (!isStandardLibFunc(fn_d.name)) {
                            const ret_str = try self.mapTypeRef(fn_d.ret_type);
                            var param_buf: std.ArrayList(u8) = .{};
                            for (fn_d.params, 0..) |p, p_idx| {
                                const pt_str = try self.mapTypeRef(p.type_ref);
                                if (p_idx > 0) try param_buf.appendSlice(self.allocator, ", ");
                                try param_buf.appendSlice(self.allocator, pt_str);
                                if (p.name.len > 0) {
                                    try param_buf.append(self.allocator, ' ');
                                    try param_buf.appendSlice(self.allocator, p.name);
                                }
                            }
                            if (fn_d.is_varargs) {
                                if (fn_d.params.len > 0) try param_buf.appendSlice(self.allocator, ", ");
                                try param_buf.appendSlice(self.allocator, "...");
                            }
                            const p_str = if (param_buf.items.len > 0) param_buf.items else "void";
                            try self.writeLineFmt("extern {s} {s}({s});", .{ ret_str, fn_d.name, p_str });
                        }
                    } else {
                        const mangled = try self.getMangledFnName(m, fn_d.name);
                        const ret_str = try self.mapTypeRef(fn_d.ret_type);
                        var param_buf: std.ArrayList(u8) = .{};
                        for (fn_d.params, 0..) |p, p_idx| {
                            const pt_str = try self.mapTypeRef(p.type_ref);
                            if (p_idx > 0) try param_buf.appendSlice(self.allocator, ", ");
                            try param_buf.appendSlice(self.allocator, pt_str);
                            try param_buf.append(self.allocator, ' ');
                            try param_buf.appendSlice(self.allocator, p.name);
                        }
                        const p_str = if (param_buf.items.len > 0) param_buf.items else "void";
                        try self.writeLineFmt("{s} {s}({s});", .{ ret_str, mangled, p_str });
                    }
                }
            }
        }
        try self.writeLine("");

        // Function bodies
        try self.writeLine("// --- Function Bodies ---");
        for (all_modules.items) |m| {
            for (m.program.statements) |stmt| {
                if (stmt.kind == .fn_decl and !stmt.data.fn_decl.is_extern) {
                    const fn_d = stmt.data.fn_decl;
                    const mangled = try self.getMangledFnName(m, fn_d.name);
                    const ret_str = try self.mapTypeRef(fn_d.ret_type);

                    var param_buf: std.ArrayList(u8) = .{};
                    for (fn_d.params, 0..) |p, p_idx| {
                        const pt_str = try self.mapTypeRef(p.type_ref);
                        if (p_idx > 0) try param_buf.appendSlice(self.allocator, ", ");
                        try param_buf.appendSlice(self.allocator, pt_str);
                        try param_buf.append(self.allocator, ' ');
                        try param_buf.appendSlice(self.allocator, p.name);
                    }
                    const p_str = if (param_buf.items.len > 0) param_buf.items else "void";

                    try self.writeLineFmt("{s} {s}({s}) {{", .{ ret_str, mangled, p_str });
                    self.indent += 1;
                    if (fn_d.body) |body| {
                        try self.emitStatement(m, body.*);
                    }
                    self.indent -= 1;
                    try self.writeLine("}");
                    try self.writeLine("");
                }
            }
        }

        // Top-level statements in main()
        try self.writeLine("int main(int argc, char** argv) {");
        self.indent += 1;

        // Emit top-level statements from root module
        for (self.root_module.program.statements) |stmt| {
            switch (stmt.kind) {
                .fn_decl, .struct_decl, .enum_decl, .import_stmt, .from_import_stmt => {},
                else => try self.emitStatement(self.root_module, stmt),
            }
        }

        try self.writeLine("return 0;");
        self.indent -= 1;
        try self.writeLine("}");

        return self.out.toOwnedSlice(self.allocator);
    }

    fn getMangledFnName(self: *Codegen, m: *Module, name: []const u8) ![]const u8 {
        if (std.mem.eql(u8, name, "main")) return "main";
        return try std.fmt.allocPrint(self.allocator, "kale_{s}_{s}", .{ m.name, name });
    }

    fn emitStatement(self: *Codegen, m: *Module, stmt: ast.Stmt) anyerror!void {
        switch (stmt.kind) {
            .block => {
                try self.writeLine("{");
                self.indent += 1;
                for (stmt.data.block) |s| {
                    try self.emitStatement(m, s);
                }
                self.indent -= 1;
                try self.writeLine("}");
            },
            .var_decl => {
                const vd = stmt.data.var_decl;
                var t_str: []const u8 = "int64_t";
                if (vd.type_ref) |tr| {
                    t_str = try self.mapTypeRef(tr);
                }
                if (vd.init) |init_e| {
                    const init_str = try self.emitExpr(m, init_e.*);
                    try self.writeLineFmt("{s} {s} = {s};", .{ t_str, vd.name, init_str });
                } else {
                    try self.writeLineFmt("{s} {s};", .{ t_str, vd.name });
                }
            },
            .if_stmt => {
                const if_s = stmt.data.if_stmt;
                const cond_str = try self.emitExpr(m, if_s.cond.*);
                try self.writeLineFmt("if ({s}) {{", .{cond_str});
                self.indent += 1;
                try self.emitStatement(m, if_s.then_stmt.*);
                self.indent -= 1;
                if (if_s.else_stmt) |else_s| {
                    try self.writeLine("} else {");
                    self.indent += 1;
                    try self.emitStatement(m, else_s.*);
                    self.indent -= 1;
                }
                try self.writeLine("}");
            },
            .while_stmt => {
                const ws = stmt.data.while_stmt;
                const cond_str = try self.emitExpr(m, ws.cond.*);
                try self.writeLineFmt("while ({s}) {{", .{cond_str});
                self.indent += 1;
                try self.emitStatement(m, ws.body.*);
                self.indent -= 1;
                try self.writeLine("}");
            },
            .for_stmt => {
                const fs = stmt.data.for_stmt;
                var init_buf: []const u8 = "";
                if (fs.init) |i_stmt| {
                    if (i_stmt.kind == .var_decl) {
                        const vd = i_stmt.data.var_decl;
                        const t_str = if (vd.type_ref) |tr| try self.mapTypeRef(tr) else "int64_t";
                        const val_str = if (vd.init) |ie| try self.emitExpr(m, ie.*) else "0";
                        init_buf = try std.fmt.allocPrint(self.allocator, "{s} {s} = {s}", .{ t_str, vd.name, val_str });
                    } else if (i_stmt.kind == .expr_stmt) {
                        init_buf = try self.emitExpr(m, i_stmt.data.expr_stmt.*);
                    }
                }
                const cond_str = if (fs.cond) |c| try self.emitExpr(m, c.*) else "";
                const inc_str = if (fs.inc) |i| try self.emitExpr(m, i.*) else "";

                try self.writeLineFmt("for ({s}; {s}; {s}) {{", .{ init_buf, cond_str, inc_str });
                self.indent += 1;
                try self.emitStatement(m, fs.body.*);
                self.indent -= 1;
                try self.writeLine("}");
            },
            .switch_stmt => {
                const sw = stmt.data.switch_stmt;
                const cond_str = try self.emitExpr(m, sw.expr.*);
                try self.writeLineFmt("switch ({s}) {{", .{cond_str});
                self.indent += 1;
                for (sw.cases) |c| {
                    for (c.values) |v| {
                        const v_str = try self.emitExpr(m, v);
                        try self.writeLineFmt("case {s}:", .{v_str});
                    }
                    self.indent += 1;
                    for (c.body) |bs| {
                        try self.emitStatement(m, bs);
                    }
                    self.indent -= 1;
                }
                if (sw.default_body) |db| {
                    try self.writeLine("default:");
                    self.indent += 1;
                    for (db) |bs| {
                        try self.emitStatement(m, bs);
                    }
                    self.indent -= 1;
                }
                self.indent -= 1;
                try self.writeLine("}");
            },
            .return_stmt => {
                if (stmt.data.return_stmt) |r_expr| {
                    const e_str = try self.emitExpr(m, r_expr.*);
                    try self.writeLineFmt("return {s};", .{e_str});
                } else {
                    try self.writeLine("return;");
                }
            },
            .break_stmt => try self.writeLine("break;"),
            .continue_stmt => try self.writeLine("continue;"),
            .print_stmt => {
                const args = stmt.data.print_stmt;
                for (args, 0..) |arg, a_idx| {
                    const arg_str = try self.emitExpr(m, arg);
                    // Determine print format based on arg
                    if (arg.kind == .literal and arg.data.literal == .str_val) {
                        try self.writeLineFmt("_kale_print_str({s});", .{arg_str});
                    } else {
                        try self.writeLineFmt("_kale_print_int({s});", .{arg_str});
                    }
                    if (a_idx < args.len - 1) {
                        try self.writeLine("_kale_print_str(\" \");");
                    }
                }
                try self.writeLine("_kale_println();");
            },
            .free_stmt => {
                const e_str = try self.emitExpr(m, stmt.data.free_stmt.*);
                try self.writeLineFmt("free((void*)({s}));", .{e_str});
            },
            .expr_stmt => {
                const e_str = try self.emitExpr(m, stmt.data.expr_stmt.*);
                try self.writeLineFmt("{s};", .{e_str});
            },
            else => {},
        }
    }

    fn emitExpr(self: *Codegen, m: *Module, expr: ast.Expr) anyerror![]const u8 {
        switch (expr.data) {
            .literal => |lit| {
                switch (lit) {
                    .int_val => |val| return try std.fmt.allocPrint(self.allocator, "{d}LL", .{val}),
                    .float_val => |fval| return try std.fmt.allocPrint(self.allocator, "{d}", .{fval}),
                    .str_val => |s| {
                        var buf: std.ArrayList(u8) = .{};
                        try buf.append(self.allocator, '"');
                        for (s) |c| {
                            switch (c) {
                                '\n' => try buf.appendSlice(self.allocator, "\\n"),
                                '\t' => try buf.appendSlice(self.allocator, "\\t"),
                                '\r' => try buf.appendSlice(self.allocator, "\\r"),
                                '\"' => try buf.appendSlice(self.allocator, "\\\""),
                                '\\' => try buf.appendSlice(self.allocator, "\\\\"),
                                0 => try buf.appendSlice(self.allocator, "\\0"),
                                else => try buf.append(self.allocator, c),
                            }
                        }
                        try buf.append(self.allocator, '"');
                        return buf.toOwnedSlice(self.allocator);
                    },
                    .char_val => |c| return try std.fmt.allocPrint(self.allocator, "{d}", .{c}),
                    .bool_val => |b| return if (b) "true" else "false",
                    .null_val => return "NULL",
                }
            },
            .variable => |v_name| {
                // Check if variable is a function name in this module or extern
                if (m.scope.lookup(v_name)) |sym| {
                    if (sym.kind == .function) {
                        return sym.mangled_name;
                    }
                }
                return v_name;
            },
            .grouping => |inner| {
                const s = try self.emitExpr(m, inner.*);
                return try std.fmt.allocPrint(self.allocator, "({s})", .{s});
            },
            .unary => |un| {
                const op_str = switch (un.op) {
                    .minus => "-",
                    .bang => "!",
                    .tilde => "~",
                    .amp => "&",
                    .star => "*",
                    .plus_plus => "++",
                    .minus_minus => "--",
                    .caret => "*",
                    else => "-",
                };
                const operand_str = try self.emitExpr(m, un.operand.*);
                if (un.is_postfix) {
                    if (un.op == .caret) {
                        return try std.fmt.allocPrint(self.allocator, "(*({s}))", .{operand_str});
                    }
                    return try std.fmt.allocPrint(self.allocator, "({s}{s})", .{ operand_str, op_str });
                }
                return try std.fmt.allocPrint(self.allocator, "({s}({s}))", .{ op_str, operand_str });
            },
            .binary => |bin| {
                const l_str = try self.emitExpr(m, bin.left.*);
                const r_str = try self.emitExpr(m, bin.right.*);
                if (bin.op == .star_star) {
                    return try std.fmt.allocPrint(self.allocator, "pow((double)({s}), (double)({s}))", .{ l_str, r_str });
                }
                const op_str = switch (bin.op) {
                    .plus => "+",
                    .minus => "-",
                    .star => "*",
                    .slash => "/",
                    .percent => "%",
                    .eq_eq => "==",
                    .bang_eq => "!=",
                    .lt => "<",
                    .lt_eq => "<=",
                    .gt => ">",
                    .gt_eq => ">=",
                    .amp_amp => "&&",
                    .pipe_pipe => "||",
                    .amp => "&",
                    .pipe => "|",
                    .caret => "^",
                    .shl => "<<",
                    .shr => ">>",
                    else => "+",
                };
                return try std.fmt.allocPrint(self.allocator, "({s} {s} {s})", .{ l_str, op_str, r_str });
            },
            .call => |c| {
                var callee_str: []const u8 = "";

                // Check if call is module-qualified: alias.func(args)
                if (c.callee.kind == .member and !c.callee.data.member.is_arrow and c.callee.data.member.target.kind == .variable) {
                    const mod_alias = c.callee.data.member.target.data.variable;
                    const fn_name = c.callee.data.member.member;

                    if (m.scope.lookup(mod_alias)) |mod_sym| {
                        if (mod_sym.module) |target_mod| {
                            callee_str = try self.getMangledFnName(target_mod, fn_name);
                        } else {
                            callee_str = try std.fmt.allocPrint(self.allocator, "kale_{s}_{s}", .{ mod_alias, fn_name });
                        }
                    } else {
                        callee_str = try std.fmt.allocPrint(self.allocator, "kale_{s}_{s}", .{ mod_alias, fn_name });
                    }
                } else if (c.callee.kind == .variable) {
                    const fn_name = c.callee.data.variable;
                    if (m.scope.lookup(fn_name)) |sym| {
                        callee_str = sym.mangled_name;
                    } else {
                        callee_str = try self.getMangledFnName(m, fn_name);
                    }
                } else {
                    callee_str = try self.emitExpr(m, c.callee.*);
                }

                var args_buf: std.ArrayList(u8) = .{};
                for (c.args, 0..) |arg, idx| {
                    const a_str = try self.emitExpr(m, arg);
                    if (idx > 0) try args_buf.appendSlice(self.allocator, ", ");
                    try args_buf.appendSlice(self.allocator, a_str);
                }

                return try std.fmt.allocPrint(self.allocator, "{s}({s})", .{ callee_str, args_buf.items });
            },
            .index => |idx| {
                const t_str = try self.emitExpr(m, idx.target.*);
                const i_str = try self.emitExpr(m, idx.index.*);
                return try std.fmt.allocPrint(self.allocator, "{s}[{s}]", .{ t_str, i_str });
            },
            .member => |mem| {
                // If member access on a module alias (e.g. tok.TOK_INT()), not an instance member
                if (!mem.is_arrow and mem.target.kind == .variable) {
                    const v_name = mem.target.data.variable;
                    if (m.scope.lookup(v_name)) |sym| {
                        if (sym.kind == .module_alias) {
                            if (sym.module) |target_mod| {
                                return try self.getMangledFnName(target_mod, mem.member);
                            }
                            return try std.fmt.allocPrint(self.allocator, "kale_{s}_{s}", .{ v_name, mem.member });
                        }
                    }
                }

                const t_str = try self.emitExpr(m, mem.target.*);
                const op = if (mem.is_arrow) "->" else ".";
                return try std.fmt.allocPrint(self.allocator, "{s}{s}{s}", .{ t_str, op, mem.member });
            },
            .assign => |asgn| {
                const t_str = try self.emitExpr(m, asgn.target.*);
                const v_str = try self.emitExpr(m, asgn.value.*);
                const op_str = switch (asgn.op) {
                    .eq => "=",
                    .plus_eq => "+=",
                    .minus_eq => "-=",
                    .star_eq => "*=",
                    .slash_eq => "/=",
                    .percent_eq => "%=",
                    .amp_eq => "&=",
                    .pipe_eq => "|=",
                    .caret_eq => "^=",
                    .shl_eq => "<<=",
                    .shr_eq => ">>=",
                    else => "=",
                };
                return try std.fmt.allocPrint(self.allocator, "{s} {s} {s}", .{ t_str, op_str, v_str });
            },
            .cast => |c| {
                const t_str = try self.mapTypeRef(c.target_type);
                const e_str = try self.emitExpr(m, c.expr.*);
                return try std.fmt.allocPrint(self.allocator, "((({s})({s})))", .{ t_str, e_str });
            },
            .alloc => |al| {
                const t_str = try self.mapTypeRef(al.type_ref);
                if (al.count) |cnt| {
                    const c_str = try self.emitExpr(m, cnt.*);
                    return try std.fmt.allocPrint(self.allocator, "(({s}*)malloc(sizeof({s}) * ({s})))", .{ t_str, t_str, c_str });
                } else {
                    return try std.fmt.allocPrint(self.allocator, "(({s}*)malloc(sizeof({s})))", .{ t_str, t_str });
                }
            },
            .array_literal => |arr| {
                var elem_type_str: []const u8 = "int64_t";
                if (arr.elements.len > 0) {
                    const first = arr.elements[0];
                    if (first.kind == .literal) {
                        switch (first.data.literal) {
                            .str_val => elem_type_str = "const char*",
                            .float_val => elem_type_str = "double",
                            .char_val => elem_type_str = "char",
                            .bool_val => elem_type_str = "bool",
                            else => elem_type_str = "int64_t",
                        }
                    } else if (first.kind == .cast) {
                        elem_type_str = try self.mapTypeRef(first.data.cast.target_type);
                    }
                }

                var buf: std.ArrayList(u8) = .{};
                for (arr.elements, 0..) |elem, idx| {
                    const el_str = try self.emitExpr(m, elem);
                    if (idx > 0) try buf.appendSlice(self.allocator, ", ");
                    try buf.appendSlice(self.allocator, el_str);
                }
                return try std.fmt.allocPrint(self.allocator, "((({s}[]){{{s}}}))", .{ elem_type_str, buf.items });
            },
        }
    }
};
