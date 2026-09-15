const std = @import("std");
const lexer_mod = @import("lexer.zig");
const parser_mod = @import("parser.zig");
const checker_mod = @import("checker.zig");
const codegen_mod = @import("codegen.zig");
const compiler_mod = @import("compiler.zig");

pub fn printUsage() void {
    std.debug.print(
        \\ZigKale v0.1.0 - High Performance Native Kale Compiler
        \\Usage: zigkale <command> [options] <input.kl>
        \\
        \\Commands:
        \\  build <file> [-o <out>] [--emit-c]    Compile Kale program to native executable
        \\  run <file> [-- <args...>]             Compile and run Kale program
        \\  check <file>                          Perform lexical, syntax, and semantic checks
        \\  dump-tokens <file>                    Tokenize and display tokens
        \\  dump-ast <file>                       Parse and display AST
        \\  dump-c <file>                         Transpile to C code and output to stdout
        \\
        \\Options:
        \\  -o <path>                             Specify output executable path
        \\  --emit-c                              Keep generated C source code
        \\  --help, -h                            Show this help message
        \\  --version, -v                         Show version information
        \\
    , .{});
}

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    const args = try std.process.argsAlloc(allocator);

    if (args.len < 2) {
        printUsage();
        return;
    }

    const first_arg = args[1];
    if (std.mem.eql(u8, first_arg, "--help") or std.mem.eql(u8, first_arg, "-h")) {
        printUsage();
        return;
    }
    if (std.mem.eql(u8, first_arg, "--version") or std.mem.eql(u8, first_arg, "-v")) {
        std.debug.print("ZigKale v0.1.0\n", .{});
        return;
    }

    var command: []const u8 = "build";
    var arg_start: usize = 1;

    if (std.mem.eql(u8, first_arg, "build") or
        std.mem.eql(u8, first_arg, "run") or
        std.mem.eql(u8, first_arg, "check") or
        std.mem.eql(u8, first_arg, "dump-tokens") or
        std.mem.eql(u8, first_arg, "dump-ast") or
        std.mem.eql(u8, first_arg, "dump-c"))
    {
        command = first_arg;
        arg_start = 2;
    }

    var input_file: ?[]const u8 = null;
    var output_file: ?[]const u8 = null;
    var emit_c: bool = false;

    var i: usize = arg_start;
    while (i < args.len) : (i += 1) {
        const arg = args[i];
        if (std.mem.eql(u8, arg, "-o")) {
            if (i + 1 < args.len) {
                output_file = args[i + 1];
                i += 1;
            } else {
                std.debug.print("Error: missing argument after -o\n", .{});
                return;
            }
        } else if (std.mem.eql(u8, arg, "--emit-c")) {
            emit_c = true;
        } else if (std.mem.eql(u8, arg, "--")) {
            break;
        } else if (!std.mem.startsWith(u8, arg, "-")) {
            input_file = arg;
        }
    }

    if (input_file == null) {
        printUsage();
        return;
    }

    const input_path = input_file.?;

    if (std.mem.eql(u8, command, "dump-tokens")) {
        const file = try std.fs.cwd().openFile(input_path, .{});
        defer file.close();
        const src = try file.readToEndAlloc(allocator, 10 * 1024 * 1024);

        var lexer = lexer_mod.Lexer.init(allocator, src);
        const tokens = try lexer.tokenizeAll();
        for (tokens) |tok| {
            std.debug.print("{s:<20} {s:<20} line {d}:{d}\n", .{ @tagName(tok.kind), tok.text, tok.line, tok.col });
        }
        return;
    }

    if (std.mem.eql(u8, command, "dump-ast")) {
        const file = try std.fs.cwd().openFile(input_path, .{});
        defer file.close();
        const src = try file.readToEndAlloc(allocator, 10 * 1024 * 1024);

        var lexer = lexer_mod.Lexer.init(allocator, src);
        const tokens = try lexer.tokenizeAll();
        var parser = parser_mod.Parser.init(allocator, tokens);
        const prog = try parser.parseProgram();

        std.debug.print("Parsed {d} top-level statement(s).\n", .{prog.statements.len});
        for (prog.statements, 0..) |s, idx| {
            std.debug.print("  [{d}] {s}\n", .{ idx, @tagName(s.kind) });
        }
        return;
    }

    if (std.mem.eql(u8, command, "dump-c")) {
        var compiler = compiler_mod.Compiler.init(allocator);
        const c_code = try compiler.compileToC(input_path);
        std.debug.print("{s}", .{c_code});
        return;
    }

    if (std.mem.eql(u8, command, "check")) {
        var compiler = compiler_mod.Compiler.init(allocator);
        _ = try compiler.compileToC(input_path);
        std.debug.print("Check passed: '{s}' is valid.\n", .{input_path});
        return;
    }

    if (std.mem.eql(u8, command, "build") or std.mem.eql(u8, command, "run")) {
        var out_exe = output_file;
        if (out_exe == null) {
            var base_name = input_path;
            if (std.mem.endsWith(u8, base_name, ".kl")) {
                base_name = base_name[0 .. base_name.len - 3];
            }
            out_exe = try std.fmt.allocPrint(allocator, "{s}.exe", .{base_name});
        }

        var compiler = compiler_mod.Compiler.init(allocator);
        try compiler.buildExecutable(input_path, out_exe.?, emit_c);
        std.debug.print("Compiled executable (ZigKale): {s}\n", .{out_exe.?});

        if (std.mem.eql(u8, command, "run")) {
            const run_argv = [_][]const u8{out_exe.?};
            const result = try std.process.Child.run(.{
                .allocator = allocator,
                .argv = &run_argv,
            });
            std.debug.print("{s}", .{result.stdout});
            if (result.stderr.len > 0) {
                std.debug.print("{s}", .{result.stderr});
            }
        }
    }
}
