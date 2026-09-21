import sys
import os
import argparse
import subprocess
from typing import Any, List, Optional

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

from .pm.manifest import Manifest, find_manifest
from .pm.project import create_project, init_project
from .pm.pack import pack_project
from .pm.registry import RegistryClient, RegistryServer

from .tools.fmt import run_fmt
from .tools.lint import run_lint
from .tools.doc import run_doc
from .tools.repl import run_repl
from .tools.test_runner import run_tests

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


def _create_module_loader(diagnostics: DiagnosticBag, current_file: str | None = None, extra_includes: list[str] | None = None) -> ModuleLoader:
    search_paths: list[str] = [os.path.abspath(".")]
    if extra_includes:
        for inc in extra_includes:
            abs_inc = os.path.abspath(inc)
            if abs_inc not in search_paths:
                search_paths.append(abs_inc)
    if current_file:
        file_dir = os.path.dirname(os.path.abspath(current_file))
        if file_dir not in search_paths:
            search_paths.append(file_dir)

    # If in a repo, add packages/std, packages, and libs to search paths
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/kale -> src -> root
    repo_root = os.path.dirname(repo_root)
    std_dir = os.path.join(repo_root, "packages", "std")
    libs_dir = os.path.join(repo_root, "libs")
    if os.path.isdir(std_dir) and std_dir not in search_paths:
        search_paths.append(std_dir)
    if os.path.isdir(libs_dir) and libs_dir not in search_paths:
        search_paths.append(libs_dir)
    if os.path.isdir(repo_root) and repo_root not in search_paths:
        search_paths.append(repo_root)

    return ModuleLoader(diagnostics, search_paths=search_paths)


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

    loader = _create_module_loader(diagnostics, args.file)
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
    file_to_check = getattr(args, "file", None)
    if not file_to_check:
        manifest_path = find_manifest()
        if manifest_path:
            manifest = Manifest.load(manifest_path)
            file_to_check = manifest.entry if os.path.isabs(manifest.entry) else os.path.join(manifest.project_dir, manifest.entry)
        else:
            print("Error: No file specified and no kale.toml found.", file=sys.stderr)
            return 1

    source_text = _read_source(file_to_check)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    extra_includes = getattr(args, "includes", []) or []
    manifest_path = find_manifest(os.path.dirname(os.path.abspath(file_to_check)))
    if manifest_path:
        manifest = Manifest.load(manifest_path)
        for inc in manifest.get_all_include_dirs():
            if inc not in extra_includes:
                extra_includes.append(inc)

    loader = _create_module_loader(diagnostics, file_to_check, extra_includes=extra_includes)
    binder = Binder(diagnostics, module_loader=loader, current_file=file_to_check)
    binder.bind_program(unit)

    if diagnostics:
        _print_diagnostics(source_text, diagnostics)
        if diagnostics.has_errors:
            return 1

    print(f"Check passed: '{file_to_check}' is valid.")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    manifest: Optional[Manifest] = None
    if not getattr(args, "file", None):
        manifest_path = find_manifest()
        if not manifest_path:
            print("Error: No source file specified and no kale.toml found in current or parent directories.", file=sys.stderr)
            return 1
        manifest = Manifest.load(manifest_path)
        project_dir = manifest.project_dir
        entry_path = manifest.entry if os.path.isabs(manifest.entry) else os.path.join(project_dir, manifest.entry)
        if not os.path.isfile(entry_path):
            print(f"Error: Project entry file not found: '{entry_path}'", file=sys.stderr)
            return 1
        args.file = entry_path

        # Backend from manifest if not overridden by explicit CLI argument
        if getattr(args, "backend", None) is None:
            args.backend = manifest.build_backend or "llvm"

        # Opt level from manifest if not overridden by explicit CLI argument
        if getattr(args, "opt", None) is None:
            args.opt = manifest.build_opt if manifest.build_opt is not None else 2

        # Output binary path
        if not getattr(args, "output", None):
            if manifest.build_output:
                out_path = manifest.build_output if os.path.isabs(manifest.build_output) else os.path.join(project_dir, manifest.build_output)
                args.output = out_path
            else:
                args.output = os.path.join(project_dir, "bin", manifest.name)

        # Merge libs
        merged_libs = list(getattr(args, "libs", []) or [])
        for l in manifest.build_libs:
            if l not in merged_libs:
                merged_libs.append(l)
        args.libs = merged_libs

        # Merge lib-dirs
        merged_lib_dirs = list(getattr(args, "lib_dirs", []) or [])
        for ld in manifest.build_lib_dirs:
            abs_ld = ld if os.path.isabs(ld) else os.path.join(project_dir, ld)
            if abs_ld not in merged_lib_dirs:
                merged_lib_dirs.append(abs_ld)
        args.lib_dirs = merged_lib_dirs

        # Merge includes
        merged_includes = list(getattr(args, "includes", []) or [])
        for inc in manifest.get_all_include_dirs(project_dir):
            if inc not in merged_includes:
                merged_includes.append(inc)
        args.includes = merged_includes
    else:
        # File was explicitly passed; if kale.toml exists nearby, load dependency includes
        file_dir = os.path.dirname(os.path.abspath(args.file))
        manifest_path = find_manifest(file_dir)
        if manifest_path:
            try:
                manifest = Manifest.load(manifest_path)
                merged_includes = list(getattr(args, "includes", []) or [])
                for inc in manifest.get_all_include_dirs(manifest.project_dir):
                    if inc not in merged_includes:
                        merged_includes.append(inc)
                args.includes = merged_includes
            except Exception:
                pass

    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    extra_includes = getattr(args, "includes", []) or []
    loader = _create_module_loader(diagnostics, args.file, extra_includes=extra_includes)
    binder = Binder(diagnostics, module_loader=loader, current_file=args.file)
    program = binder.bind_program(unit)

    if diagnostics.has_errors:
        _print_diagnostics(source_text, diagnostics)
        return 1

    backend = getattr(args, "backend", None) or "llvm"
    base_name, _ = os.path.splitext(args.file)

    # Ensure output directory exists if output path given
    if getattr(args, "output", None):
        out_dir = os.path.dirname(os.path.abspath(args.output))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    if backend == "llvm":
        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        ll_code = str(mod)

        ll_path = f"{base_name}.ll"
        with open(ll_path, "w", encoding="utf-8") as f:
            f.write(ll_code)

        if getattr(args, "emit_llvm", False):
            print(f"Generated LLVM IR: {ll_path}")

        if getattr(args, "no_compile", False):
            return 0

        try:
            driver = LLVMDriver()
            out_exe = args.output or None
            opt_level = getattr(args, "opt", None) if getattr(args, "opt", None) is not None else 2
            extra_libs = getattr(args, "libs", []) or []
            lib_dirs = getattr(args, "lib_dirs", []) or []
            binary = driver.compile_ll(
                ll_path,
                out_exe,
                opt_level=opt_level,
                extra_libs=extra_libs,
                lib_dirs=lib_dirs,
            )
            print(f"Compiled executable (LLVM): {binary}")
            return 0
        except Exception as e:
            print(f"Build error: {e}", file=sys.stderr)
            return 1
        finally:
            if not getattr(args, "emit_llvm", False) and os.path.exists(ll_path):
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
    target = getattr(args, "target", None) or getattr(args, "file", None)
    manifest_path = find_manifest()
    manifest = Manifest.load(manifest_path) if manifest_path else None

    # Check if target is a script in kale.toml
    if target:
        if manifest and target in manifest.scripts:
            cmd = manifest.scripts[target]
            extra = getattr(args, "extra_args", []) or []
            if extra:
                cmd = f"{cmd} {subprocess.list2cmdline(extra)}"
            print(f"> {cmd}")
            res = subprocess.run(cmd, shell=True, cwd=manifest.project_dir)
            return res.returncode

        # If not a script, check if target is an existing source file or .kl file
        if os.path.isfile(target) or target.endswith(".kl"):
            args.file = target
        else:
            if manifest:
                available = ", ".join(manifest.scripts.keys())
                print(f"Error: '{target}' is neither a recognized script in kale.toml nor an existing source file.", file=sys.stderr)
                if available:
                    print(f"Available scripts: {available}", file=sys.stderr)
            else:
                print(f"Error: file not found: '{target}'", file=sys.stderr)
            return 1
    else:
        # No target provided
        if manifest:
            if "start" in manifest.scripts:
                cmd = manifest.scripts["start"]
                extra = getattr(args, "extra_args", []) or []
                if extra:
                    cmd = f"{cmd} {subprocess.list2cmdline(extra)}"
                print(f"> {cmd}")
                res = subprocess.run(cmd, shell=True, cwd=manifest.project_dir)
                return res.returncode
            else:
                entry_path = manifest.entry if os.path.isabs(manifest.entry) else os.path.join(manifest.project_dir, manifest.entry)
                if os.path.isfile(entry_path):
                    args.file = entry_path
                else:
                    print(f"Error: Project entry file '{manifest.entry}' not found in project.", file=sys.stderr)
                    return 1
        else:
            print("Error: No source file specified and no kale.toml found in current or parent directories.", file=sys.stderr)
            return 1

    # Running a .kl source file
    extra_includes = list(getattr(args, "includes", []) or [])
    if manifest:
        for inc in manifest.get_all_include_dirs(manifest.project_dir):
            if inc not in extra_includes:
                extra_includes.append(inc)

    source_text = _read_source(args.file)
    if source_text is None:
        return 1

    diagnostics = DiagnosticBag()
    parser = Parser(source_text, diagnostics)
    unit = parser.parse_compilation_unit()

    loader = _create_module_loader(diagnostics, args.file, extra_includes=extra_includes)
    binder = Binder(diagnostics, module_loader=loader, current_file=args.file)
    program = binder.bind_program(unit)

    if diagnostics.has_errors:
        _print_diagnostics(source_text, diagnostics)
        return 1

    backend = args.backend if getattr(args, "backend", None) is not None else ((manifest.build_backend if manifest else None) or "llvm")
    opt = args.opt if getattr(args, "opt", None) is not None else ((manifest.build_opt if manifest else None) or 2)

    if backend == "llvm":
        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        jit = LLVMJIT(opt_level=opt)
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
            res = c_driver.run(binary, getattr(args, "extra_args", []))
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


def cmd_new(args: argparse.Namespace) -> int:
    try:
        dest = create_project(
            name=args.name,
            target_dir=getattr(args, "path", None),
            is_lib=getattr(args, "lib", False),
        )
        proj_type = "library" if args.lib else "project"
        print(f"Created new Kale {proj_type} '{args.name}' in {dest}")
        return 0
    except Exception as e:
        print(f"Error creating project: {e}", file=sys.stderr)
        return 1


def cmd_init(args: argparse.Namespace) -> int:
    try:
        manifest_path = init_project(
            dir_path=".",
            is_lib=getattr(args, "lib", False),
            name=getattr(args, "name", None),
        )
        print(f"Initialized Kale project in {manifest_path}")
        return 0
    except Exception as e:
        print(f"Error initializing project: {e}", file=sys.stderr)
        return 1


def cmd_add(args: argparse.Namespace) -> int:
    manifest_path = find_manifest()
    if not manifest_path:
        print("Error: No kale.toml found in current or parent directories.", file=sys.stderr)
        return 1

    manifest = Manifest.load(manifest_path)
    pkg = args.pkg
    spec: Any = "*"

    if getattr(args, "path", None):
        spec = {"path": args.path}
    elif getattr(args, "version", None):
        spec = args.version
    elif "@" in pkg:
        pkg, spec = pkg.split("@", 1)
    else:
        # Check if registry has the package to resolve latest version (like bun/uv/npm)
        try:
            client = RegistryClient(registry_url=getattr(args, "registry", None))
            info = client.info(pkg)
            latest = info.get("latest") or info.get("version")
            if latest:
                spec = f"^{latest}"
        except Exception:
            spec = "*"

    manifest.add_dependency(pkg, spec, dev=getattr(args, "dev", False))
    manifest.save()
    dep_type = "dev-dependency" if args.dev else "dependency"
    print(f"Added {dep_type} '{pkg}' = {spec} to {manifest_path}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    manifest_path = find_manifest()
    if not manifest_path:
        print("Error: No kale.toml found in current or parent directories.", file=sys.stderr)
        return 1

    manifest = Manifest.load(manifest_path)
    if manifest.remove_dependency(args.pkg):
        manifest.save()
        print(f"Removed dependency '{args.pkg}' from {manifest_path}")
        return 0
    else:
        print(f"Error: Dependency '{args.pkg}' not found in kale.toml.", file=sys.stderr)
        return 1


def cmd_pack(args: argparse.Namespace) -> int:
    manifest_path = find_manifest()
    if not manifest_path:
        print("Error: No kale.toml found in current or parent directories.", file=sys.stderr)
        return 1

    proj_dir = os.path.dirname(os.path.abspath(manifest_path))
    try:
        archive_path, checksum = pack_project(proj_dir, output_dir=getattr(args, "out", None))
        print(f"Created package: {archive_path}")
        print(f"SHA-256: {checksum}")
        return 0
    except Exception as e:
        print(f"Error packing project: {e}", file=sys.stderr)
        return 1


def cmd_publish(args: argparse.Namespace) -> int:
    pkg_target = getattr(args, "package", None)
    if not pkg_target:
        manifest_path = find_manifest()
        if not manifest_path:
            print("Error: No package archive specified and no kale.toml found in current or parent directories.", file=sys.stderr)
            return 1
        pkg_target = os.path.dirname(os.path.abspath(manifest_path))

    client = RegistryClient(
        registry_url=getattr(args, "registry", None),
        token=getattr(args, "token", None),
    )
    try:
        res = client.publish(pkg_target)
        print(f"Successfully published {res.get('package')}@{res.get('version')}")
        print(f"Registry: {client.registry_url}")
        print(f"SHA-256:  {res.get('checksum')}")
        return 0
    except Exception as e:
        print(f"Publish failed: {e}", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    client = RegistryClient(registry_url=getattr(args, "registry", None))
    query = getattr(args, "query", "") or ""
    try:
        results = client.search(query)
        if not results:
            if query:
                print(f"No packages found matching '{query}'.")
            else:
                print("No packages found in registry.")
            return 0
        header = f"Found {len(results)} package(s) matching '{query}':" if query else f"Found {len(results)} package(s) in registry:"
        print(header)
        print(f"{'PACKAGE':<25} {'VERSION':<12} {'DESCRIPTION'}")
        print("-" * 70)
        for r in results:
            desc = (r.get("description") or "")[:40]
            print(f"{r.get('name', ''):<25} {r.get('version', ''):<12} {desc}")
        return 0
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    client = RegistryClient(registry_url=getattr(args, "registry", None))
    try:
        data = client.info(args.pkg, version=getattr(args, "version", None))
        print(f"Package: {data.get('name')}")
        print(f"Latest:  {data.get('latest') or data.get('version')}")
        if data.get("description"):
            print(f"Summary: {data.get('description')}")
        if data.get("license"):
            print(f"License: {data.get('license')}")
        if data.get("authors"):
            print(f"Authors: {', '.join(data.get('authors'))}")
        if data.get("versions"):
            print(f"Versions: {', '.join(data.get('versions').keys())}")
        if data.get("dependencies"):
            print("Dependencies:")
            for k, v in data.get("dependencies").items():
                print(f"  {k}: {v}")
        return 0
    except Exception as e:
        print(f"Info request failed: {e}", file=sys.stderr)
        return 1


def cmd_whoami(args: argparse.Namespace) -> int:
    client = RegistryClient(registry_url=getattr(args, "registry", None))
    try:
        res = client.whoami()
        if res.get("authenticated"):
            print(f"Logged in as '{res.get('username')}' on {client.registry_url}")
            return 0
        else:
            print(f"Not logged in on {client.registry_url}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error checking login status: {e}", file=sys.stderr)
        return 1


def cmd_login(args: argparse.Namespace) -> int:
    client = RegistryClient(registry_url=getattr(args, "registry", None))
    try:
        token = getattr(args, "token", None)
        if not token and not getattr(args, "username", None):
            import getpass
            if sys.stdin.isatty():
                user = input("Username: ").strip() or "user"
                pwd = getpass.getpass("Password: ")
            else:
                user = "user"
                pwd = ""
            token = client.login(username=user, password=pwd)
        else:
            token = client.login(
                username=getattr(args, "username", None),
                password=getattr(args, "password", None),
                token=token,
            )
        print(f"Login successful for {client.registry_url}")
        return 0
    except Exception as e:
        print(f"Login failed: {e}", file=sys.stderr)
        return 1


def cmd_registry(args: argparse.Namespace) -> int:
    if getattr(args, "registry_command", None) == "start":
        server = RegistryServer(
            host=getattr(args, "host", "0.0.0.0"),
            port=getattr(args, "port", 8080),
            storage_dir=getattr(args, "storage_dir", ".kale_registry"),
            require_auth=getattr(args, "require_auth", False),
            verbose=True,
        )
        print(f"Starting Kale Package Registry on {args.host}:{args.port}...")
        print(f"Storage directory: {server.storage_dir}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down registry...")
            server.stop()
        return 0
    return 1


def cmd_fmt(args: argparse.Namespace) -> int:
    paths = args.paths or ["."]
    return run_fmt(paths, check=args.check)


def cmd_lint(args: argparse.Namespace) -> int:
    paths = args.paths or ["."]
    return run_lint(paths)


def cmd_doc(args: argparse.Namespace) -> int:
    paths = args.paths or ["."]
    out = args.output or "docs/API.md"
    return run_doc(paths, out_file=out)


def cmd_repl(args: argparse.Namespace) -> int:
    opt = getattr(args, "opt", 0)
    return run_repl(opt_level=opt)


def cmd_test(args: argparse.Namespace) -> int:
    targets = args.targets or ["."]
    jobs = getattr(args, "jobs", 4)
    pattern = getattr(args, "pattern", None)
    return run_tests(targets, jobs=jobs, pattern=pattern)


def main() -> int:
    parser = argparse.ArgumentParser(prog="kale", description="Kale Programming Language Compiler & Package Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    p_build = subparsers.add_parser("build", help="Compile a Kale source file or project to native binary")
    p_build.add_argument("file", nargs="?", default=None, help="Path to .kl source file (optional if kale.toml exists)")
    p_build.add_argument("-o", "--output", help="Output executable path")
    p_build.add_argument("--backend", choices=["llvm", "c"], default=None, help="Backend compiler (default: llvm or manifest build.backend)")
    p_build.add_argument("--emit-llvm", action="store_true", help="Keep generated .ll file (LLVM IR)")
    p_build.add_argument("--emit-c", action="store_true", help="Keep generated .c file")
    p_build.add_argument("--opt", type=int, choices=[0, 1, 2, 3], default=None, help="Optimization level (0-3, default: 2 or manifest build.opt)")
    p_build.add_argument("--no-compile", action="store_true", help="Generate IR/C without native binary linkage")
    p_build.add_argument("-l", "--lib", action="append", default=[], dest="libs", help="Additional libraries to link (e.g. -lglfw3)")
    p_build.add_argument("-L", "--lib-dir", action="append", default=[], dest="lib_dirs", help="Additional library search directories")
    p_build.add_argument("-I", "--include", action="append", default=[], dest="includes", help="Additional module search directories")

    # run
    p_run = subparsers.add_parser("run", help="Execute a project script or compile and run a .kl source file")
    p_run.add_argument("target", nargs="?", default=None, help="Script name in kale.toml or path to .kl source file")
    p_run.add_argument("--backend", choices=["llvm", "c"], default=None, help="Backend compiler (default: llvm or manifest build.backend)")
    p_run.add_argument("--opt", type=int, choices=[0, 1, 2, 3], default=None, help="Optimization level (0-3, default: 2 or manifest build.opt)")
    p_run.add_argument("-I", "--include", action="append", default=[], dest="includes", help="Additional module search directories")
    p_run.add_argument("extra_args", nargs="*", help="Arguments to pass to compiled program or script")

    # check
    p_check = subparsers.add_parser("check", help="Typecheck and validate without compiling")
    p_check.add_argument("file", nargs="?", default=None, help="Path to .kl source file (optional if kale.toml exists)")

    # new
    p_new = subparsers.add_parser("new", help="Bootstrap a new Kale project")
    p_new.add_argument("name", help="Name of the project")
    p_new.add_argument("--lib", action="store_true", help="Create a library project instead of an executable")
    p_new.add_argument("--path", help="Custom destination directory")

    # init
    p_init = subparsers.add_parser("init", help="Initialize kale.toml in the current directory")
    p_init.add_argument("--lib", action="store_true", help="Initialize as a library project")
    p_init.add_argument("--name", help="Project name (defaults to current directory name)")

    # add
    p_add = subparsers.add_parser("add", help="Add a dependency to kale.toml")
    p_add.add_argument("pkg", help="Package name (e.g. mylib or mylib@^1.0)")
    p_add.add_argument("--dev", action="store_true", help="Add as a dev-dependency")
    p_add.add_argument("--path", help="Local path dependency")
    p_add.add_argument("--version", help="Version constraint")
    p_add.add_argument("--registry", help="Registry URL to query for latest package version")

    # remove
    p_remove = subparsers.add_parser("remove", help="Remove a dependency from kale.toml")
    p_remove.add_argument("pkg", help="Package name to remove")

    # pack
    p_pack = subparsers.add_parser("pack", help="Create a reproducible .kale-pkg archive")
    p_pack.add_argument("-o", "--out", help="Output directory for package archive")

    # publish
    p_publish = subparsers.add_parser("publish", help="Publish a package archive to registry")
    p_publish.add_argument("package", nargs="?", default=None, help="Package archive or directory (defaults to current project)")
    p_publish.add_argument("--registry", help="Registry URL")
    p_publish.add_argument("--token", help="Registry authentication token")

    # search
    p_search = subparsers.add_parser("search", help="Search for packages in registry")
    p_search.add_argument("query", nargs="?", default="", help="Search query (leave blank to list all packages)")
    p_search.add_argument("--registry", help="Registry URL")

    # info
    p_info = subparsers.add_parser("info", help="View package details from registry")
    p_info.add_argument("pkg", help="Package name")
    p_info.add_argument("--version", help="Specific package version")
    p_info.add_argument("--registry", help="Registry URL")

    # login
    p_login = subparsers.add_parser("login", help="Authenticate with package registry")
    p_login.add_argument("--registry", help="Registry URL")
    p_login.add_argument("--token", help="Authentication token")
    p_login.add_argument("-u", "--username", help="Username")
    p_login.add_argument("-p", "--password", help="Password")

    # whoami
    p_whoami = subparsers.add_parser("whoami", help="Check active authenticated user on registry")
    p_whoami.add_argument("--registry", help="Registry URL")

    # registry
    p_registry = subparsers.add_parser("registry", help="Manage package registry server")
    reg_sub = p_registry.add_subparsers(dest="registry_command", required=True)
    p_reg_start = reg_sub.add_parser("start", help="Start the reference registry server")
    p_reg_start.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    p_reg_start.add_argument("-p", "--port", type=int, default=8080, help="Port number (default: 8080)")
    p_reg_start.add_argument("--storage-dir", default=".kale_registry", help="Package storage directory")
    p_reg_start.add_argument("--require-auth", action="store_true", help="Require authentication for publishing")

    # dump-llvm
    p_llvm = subparsers.add_parser("dump-llvm", help="Dump generated LLVM IR")
    p_llvm.add_argument("file", help="Path to .kl source file")

    # dump-ast
    p_ast = subparsers.add_parser("dump-ast", help="Dump parsed AST tree")
    p_ast.add_argument("file", help="Path to .kl source file")

    # dump-tokens
    p_tokens = subparsers.add_parser("dump-tokens", help="Dump scanned tokens")
    p_tokens.add_argument("file", help="Path to .kl source file")

    # fmt
    p_fmt = subparsers.add_parser("fmt", help="Format Kale (.kl) source files")
    p_fmt.add_argument("paths", nargs="*", default=[], help="Files or directories to format (default: current directory)")
    p_fmt.add_argument("--check", action="store_true", help="Check if files are formatted without writing")

    # lint
    p_lint = subparsers.add_parser("lint", help="Static analysis and linting for Kale source code")
    p_lint.add_argument("paths", nargs="*", default=[], help="Files or directories to lint (default: current directory)")

    # doc
    p_doc = subparsers.add_parser("doc", help="Generate API documentation from source comments")
    p_doc.add_argument("paths", nargs="*", default=[], help="Files or directories to document (default: current directory)")
    p_doc.add_argument("-o", "--output", default="docs/API.md", help="Output file path (default: docs/API.md)")

    # repl
    p_repl = subparsers.add_parser("repl", help="Start an interactive Kale REPL")
    p_repl.add_argument("--opt", type=int, choices=[0, 1, 2, 3], default=0, help="Optimization level (default: 0)")

    # test
    p_test = subparsers.add_parser("test", help="Run test suites in parallel")
    p_test.add_argument("targets", nargs="*", default=[], help="Test files or directories (default: current directory)")
    p_test.add_argument("-j", "--jobs", type=int, default=4, help="Number of concurrent test worker jobs (default: 4)")
    p_test.add_argument("-k", "--pattern", help="Filter tests by name pattern")

    args, unknown = parser.parse_known_args()

    # If running a script, allow unknown args to be passed forward
    if args.command == "run" and unknown:
        args.extra_args = list(getattr(args, "extra_args", []) or []) + unknown
    elif unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    commands = {
        "build": cmd_build,
        "run": cmd_run,
        "check": cmd_check,
        "new": cmd_new,
        "init": cmd_init,
        "add": cmd_add,
        "remove": cmd_remove,
        "pack": cmd_pack,
        "publish": cmd_publish,
        "search": cmd_search,
        "info": cmd_info,
        "login": cmd_login,
        "whoami": cmd_whoami,
        "registry": cmd_registry,
        "dump-llvm": cmd_dump_llvm,
        "dump-ast": cmd_dump_ast,
        "dump-tokens": cmd_dump_tokens,
        "fmt": cmd_fmt,
        "lint": cmd_lint,
        "doc": cmd_doc,
        "repl": cmd_repl,
        "test": cmd_test,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        return cmd_fn(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
