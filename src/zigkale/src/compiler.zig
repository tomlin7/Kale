const std = @import("std");
const checker_mod = @import("checker.zig");
const Checker = checker_mod.Checker;
const codegen_mod = @import("codegen.zig");
const Codegen = codegen_mod.Codegen;

pub const BuildOptions = struct {
    emit_c: bool = false,
    libs: []const []const u8 = &.{},
    lib_dirs: []const []const u8 = &.{},
    includes: []const []const u8 = &.{},
};

pub const Compiler = struct {
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator) Compiler {
        return .{ .allocator = allocator };
    }

    pub fn compileToC(self: *Compiler, input_path: []const u8, includes: []const []const u8) ![]const u8 {
        var checker = try Checker.init(self.allocator);

        // Add directory of input file to search paths
        if (std.fs.path.dirname(input_path)) |dir| {
            try checker.addSearchPath(dir);
        }

        // Add extra include search paths
        for (includes) |inc| {
            try checker.addSearchPath(inc);
        }

        const root_mod = try checker.loadModule(input_path);
        var codegen = Codegen.init(self.allocator, &checker, root_mod);
        return try codegen.generate();
    }

    pub fn buildExecutable(self: *Compiler, input_path: []const u8, output_exe: []const u8, options: BuildOptions) !void {
        const c_code = try self.compileToC(input_path, options.includes);

        var c_path: []const u8 = "";
        if (options.emit_c) {
            var base_name = input_path;
            if (std.mem.endsWith(u8, base_name, ".kl")) {
                base_name = base_name[0 .. base_name.len - 3];
            }
            c_path = try std.fmt.allocPrint(self.allocator, "{s}.c", .{base_name});
        } else {
            // Temporary C file alongside output executable
            if (std.fs.path.dirname(output_exe)) |dir| {
                c_path = try std.fmt.allocPrint(self.allocator, "{s}/_tmp_out.c", .{dir});
            } else {
                c_path = "_tmp_out.c";
            }
        }

        // Write C source file
        const file = try std.fs.cwd().createFile(c_path, .{});
        try file.writeAll(c_code);
        file.close();

        // Compile C file using `zig cc -O2`
        var argv: std.ArrayList([]const u8) = .{};
        try argv.append(self.allocator, "zig");
        try argv.append(self.allocator, "cc");
        try argv.append(self.allocator, "-O2");
        try argv.append(self.allocator, c_path);
        try argv.append(self.allocator, "-o");
        try argv.append(self.allocator, output_exe);
        try argv.append(self.allocator, "-lm");
        if (@import("builtin").os.tag == .windows) {
            try argv.append(self.allocator, "-lws2_32");
            try argv.append(self.allocator, "-luser32");
            try argv.append(self.allocator, "-lgdi32");
        }
        try argv.append(self.allocator, "-Wno-parentheses-equality");

        for (options.lib_dirs) |dir| {
            try argv.append(self.allocator, try std.fmt.allocPrint(self.allocator, "-L{s}", .{dir}));
        }
        for (options.libs) |lib| {
            try argv.append(self.allocator, try std.fmt.allocPrint(self.allocator, "-l{s}", .{lib}));
        }
        for (options.includes) |inc| {
            try argv.append(self.allocator, try std.fmt.allocPrint(self.allocator, "-I{s}", .{inc}));
        }

        const result = try std.process.Child.run(.{
            .allocator = self.allocator,
            .argv = argv.items,
            .max_output_bytes = 10 * 1024 * 1024,
        });

        if (result.term.Exited != 0) {
            std.debug.print("C compilation failed with code {d}:\n{s}\n{s}\n", .{
                result.term.Exited,
                result.stdout,
                result.stderr,
            });
            return error.CompilationFailed;
        }

        // Clean up temporary C file if emit_c was not requested
        if (!options.emit_c and !std.mem.eql(u8, c_path, input_path)) {
            std.fs.cwd().deleteFile(c_path) catch {};
        }
    }
};
