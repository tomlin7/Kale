const std = @import("std");
const checker_mod = @import("checker.zig");
const Checker = checker_mod.Checker;
const codegen_mod = @import("codegen.zig");
const Codegen = codegen_mod.Codegen;

pub const Compiler = struct {
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator) Compiler {
        return .{ .allocator = allocator };
    }

    pub fn compileToC(self: *Compiler, input_path: []const u8) ![]const u8 {
        var checker = try Checker.init(self.allocator);

        // Add directory of input file to search paths
        if (std.fs.path.dirname(input_path)) |dir| {
            try checker.addSearchPath(dir);
        }

        const root_mod = try checker.loadModule(input_path);
        var codegen = Codegen.init(self.allocator, &checker, root_mod);
        return try codegen.generate();
    }

    pub fn buildExecutable(self: *Compiler, input_path: []const u8, output_exe: []const u8, emit_c: bool) !void {
        const c_code = try self.compileToC(input_path);

        var c_path: []const u8 = "";
        if (emit_c) {
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
        const argv = [_][]const u8{
            "zig",
            "cc",
            "-O2",
            c_path,
            "-o",
            output_exe,
            "-lm",
        };

        const result = try std.process.Child.run(.{
            .allocator = self.allocator,
            .argv = &argv,
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
        if (!emit_c and !std.mem.eql(u8, c_path, input_path)) {
            std.fs.cwd().deleteFile(c_path) catch {};
        }
    }
};
