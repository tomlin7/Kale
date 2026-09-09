import sys
import os
import argparse
from .diagnostics.source_text import SourceText
from .diagnostics.diagnostic_bag import DiagnosticBag
from .syntax.lexer import Lexer
from .ast.printer import AstPrinter
from .parser.parser import Parser
from .binding.binder import Binder
from .binding.module_loader import ModuleLoader
from .codegen.llvm_emitter import LLVMEmitter
from .codegen.llvm_jit import LLVMJIT
from .codegen.llvm_driver import LLVMDriver
from .codegen.c_emitter import CEmitter
from .codegen.compiler_driver import CompilerDriver

# Configure UTF-8 for console output
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def _read_source(file_path: str) -> SourceText | None:
    if not os.path.isfile(file_path):
        print(f"Error: file not found: '{file_path}'", file=sys.stderr)
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return SourceText(content, file_name=file_path)
    except Exception as e:
        print(f"Error reading '{file_path}': {e}", file=sys.stderr)
        return None

def _print_diagnostics(source_text: SourceText, diagnostics: DiagnosticBag):
    for diag in diagnostics:
        print(source_text.format_diagnostic(diag), file=sys.stderr)

def cmd_dump_tokens(args: argparse.Namespace) -> int:
    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    lexer = Lexer(source_text, diagnostics)
    tokens = lexer.lex_all(include_trivia=False)

    for tok in tokens:
        print(f"{tok.kind.name:<25} {tok.text!r:<20} {tok.span}")

    if diagnostics:
        _print_diagnostics(source_text, diagnostics)
        return 1 if diagnostics.has_errors else 0
    return 0

def cmd_dump_ast(args: argparse.Namespace) -> int:
    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    printer = AstPrinter()
    print(printer.print_node(unit))

    if diagnostics:
        _print_diagnostics(source_text, diagnostics)
        return 1 if diagnostics.has_errors else 0
    return 0

def cmd_dump_llvm(args: argparse.Namespace) -> int:
    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    loader = ModuleLoader(diagnostics)
    binder = Binder(diagnostics, module_loader=loader, current_file=args.file)
    program = binder.bind_program(unit)

    if diagnostics.has_errors:
        _print_diagnostics(source_text, diagnostics)
        return 1

    emitter = LLVMEmitter()
    mod = emitter.emit_module(program)
    print(str(mod))
    return 0

def cmd_check(args: argparse.Namespace) -> int:
    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    loader = ModuleLoader(diagnostics)
    binder = Binder(diagnostics, module_loader=loader, current_file=args.file)
    binder.bind_program(unit)

    if diagnostics:
        _print_diagnostics(source_text, diagnostics)
        if diagnostics.has_errors:
            return 1

    print(f"Check passed: '{args.file}' is valid.")
    return 0

def cmd_build(args: argparse.Namespace) -> int:
    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    loader = ModuleLoader(diagnostics)
    binder = Binder(diagnostics, module_loader=loader, current_file=args.file)
    program = binder.bind_program(unit)

    if diagnostics.has_errors:
        _print_diagnostics(source_text, diagnostics)
        return 1

    backend = getattr(args, "backend", "llvm")
    base_name, _ = os.path.splitext(args.file)

    if backend == "llvm":
        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        ll_code = str(mod)

        ll_path = f"{base_name}.ll"
        with open(ll_path, "w", encoding="utf-8") as f:
            f.write(ll_code)

        if args.emit_llvm:
            print(f"Generated LLVM IR: {ll_path}")

        if getattr(args, "no_compile", False):
            return 0

        try:
            driver = LLVMDriver()
            out_exe = args.output or None
            opt_level = getattr(args, "opt", 2)
            binary = driver.compile_ll(ll_path, out_exe, opt_level=opt_level)
            print(f"Compiled executable (LLVM): {binary}")
            return 0
        except Exception as e:
            print(f"Build error: {e}", file=sys.stderr)
            return 1
        finally:
            if not args.emit_llvm and os.path.exists(ll_path):
                os.remove(ll_path)
    else:
        # C backend
        emitter = CEmitter()
        c_code = emitter.emit(program)
        c_path = f"{base_name}.c"
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(c_code)

        if getattr(args, "emit_c", False):
            print(f"Generated C source: {c_path}")

        if getattr(args, "no_compile", False):
            return 0

        try:
            c_driver = CompilerDriver()
            out_exe = args.output or None
            binary = c_driver.compile(c_path, out_exe)
            print(f"Compiled executable (C): {binary}")
            return 0
        except Exception as e:
            print(f"Build error: {e}", file=sys.stderr)
            return 1

def cmd_run(args: argparse.Namespace) -> int:
    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    loader = ModuleLoader(diagnostics)
    binder = Binder(diagnostics, module_loader=loader, current_file=args.file)
    program = binder.bind_program(unit)

    if diagnostics.has_errors:
        _print_diagnostics(source_text, diagnostics)
        return 1

    backend = getattr(args, "backend", "llvm")

    if backend == "llvm":
        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        jit = LLVMJIT(opt_level=getattr(args, "opt", 2))
        try:
            return jit.run_ir(str(mod))
        except Exception as e:
            print(f"JIT Execution error: {e}", file=sys.stderr)
            return 1
    else:
        emitter = CEmitter()
        c_code = emitter.emit(program)
        base_name, _ = os.path.splitext(args.file)
        c_path = f"{base_name}.tmp.c"
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(c_code)

        try:
            c_driver = CompilerDriver()
            binary = c_driver.compile(c_path)
            res = c_driver.run(binary, args.extra_args)
            if res.stdout:
                sys.stdout.write(res.stdout)
            if res.stderr:
                sys.stderr.write(res.stderr)
            return res.returncode
        except Exception as e:
            print(f"Execution error: {e}", file=sys.stderr)
            return 1
        finally:
            if os.path.exists(c_path):
                os.remove(c_path)
            tmp_exe = f"{base_name}.tmp.exe" if os.name == "nt" else f"{base_name}.tmp"
            if os.path.exists(tmp_exe):
                os.remove(tmp_exe)

def main() -> int:
    parser = argparse.ArgumentParser(prog="kale", description="Kale Programming Language Compiler (LLVM & Native)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    p_build = subparsers.add_parser("build", help="Compile a Kale source file to native binary")
    p_build.add_argument("file", help="Path to .kl source file")
    p_build.add_argument("-o", "--output", help="Output executable path")
    p_build.add_argument("--backend", choices=["llvm", "c"], default="llvm", help="Backend compiler (default: llvm)")
    p_build.add_argument("--emit-llvm", action="store_true", help="Keep generated .ll file (LLVM IR)")
    p_build.add_argument("--emit-c", action="store_true", help="Keep generated .c file")
    p_build.add_argument("--opt", type=int, choices=[0, 1, 2, 3], default=2, help="Optimization level (0-3)")
    p_build.add_argument("--no-compile", action="store_true", help="Generate IR/C without native binary linkage")

    # run
    p_run = subparsers.add_parser("run", help="Compile and execute (uses in-memory LLVM JIT)")
    p_run.add_argument("file", help="Path to .kl source file")
    p_run.add_argument("--backend", choices=["llvm", "c"], default="llvm", help="Backend compiler (default: llvm)")
    p_run.add_argument("--opt", type=int, choices=[0, 1, 2, 3], default=2, help="Optimization level (0-3)")
    p_run.add_argument("extra_args", nargs="*", help="Arguments to pass to compiled program")

    # check
    p_check = subparsers.add_parser("check", help="Typecheck and validate without compiling")
    p_check.add_argument("file", help="Path to .kl source file")

    # dump-llvm
    p_llvm = subparsers.add_parser("dump-llvm", help="Dump generated LLVM IR")
    p_llvm.add_argument("file", help="Path to .kl source file")

    # dump-ast
    p_ast = subparsers.add_parser("dump-ast", help="Dump parsed AST tree")
    p_ast.add_argument("file", help="Path to .kl source file")

    # dump-tokens
    p_tokens = subparsers.add_parser("dump-tokens", help="Dump scanned tokens")
    p_tokens.add_argument("file", help="Path to .kl source file")

    args = parser.parse_args()

    commands = {
        "build": cmd_build,
        "run": cmd_run,
        "check": cmd_check,
        "dump-llvm": cmd_dump_llvm,
        "dump-ast": cmd_dump_ast,
        "dump-tokens": cmd_dump_tokens,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        return cmd_fn(args)
    parser.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())
