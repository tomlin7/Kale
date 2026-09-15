import subprocess
import os
import shutil
import pytest

def test_self_hosting_compiler_driver():
    """src/kale_self/main.kl: End-to-end self-hosting compiler pipeline and CLI driver test"""
    os.makedirs("bin", exist_ok=True)
    
    # 1. Build test_kale_self_driver.kl executable
    r = subprocess.run(
        ["uv", "run", "--directory", "E:/kale", "python", "-m", "kale.cli", "build",
         "tests/test_kale_self_driver.kl", "-o", "bin/test_kale_self_driver.exe"],
        capture_output=True, text=True, cwd="E:/kale"
    )
    assert r.returncode == 0, f"Compile failed:\n{r.stdout}\n{r.stderr}"

    # 2. Run test_kale_self_driver.exe
    r2 = subprocess.run(["bin/test_kale_self_driver.exe"], capture_output=True, text=True, cwd="E:/kale")
    assert r2.returncode == 0, f"Runtime failed: code {r2.returncode}\n{r2.stdout}\n{r2.stderr}"
    assert "ALL SELF-HOSTING DRIVER TESTS PASSED PERFECTLY." in r2.stdout

    # 3. Verify output C file produced by the driver exists and is non-empty
    c_out_path = "bin/driver_sample.c"
    assert os.path.isfile(c_out_path), "Expected bin/driver_sample.c to be generated"
    with open(c_out_path, "r", encoding="utf-8") as f:
        c_content = f.read()
    assert "int64_t factorial(int64_t n)" in c_content
    assert "int64_t add(int64_t a, int64_t b)" in c_content
    assert "int64_t main()" in c_content

    # 4. Verify clang can compile the generated C code to an object file
    clang_exe = shutil.which("clang")
    if clang_exe:
        clang_res = subprocess.run(
            [clang_exe, "-c", c_out_path, "-o", "bin/driver_sample.obj"],
            capture_output=True, text=True, cwd="E:/kale"
        )
        assert clang_res.returncode == 0, f"Clang compilation of generated C code failed:\n{clang_res.stderr}"

    # 5. Clean up temporary files in bin/
    for tmp_file in [
        "bin/test_kale_self_driver.exe",
        "bin/driver_sample.kl",
        "bin/driver_sample.c",
        "bin/driver_sample.obj",
        "bin/driver_cli_output.c",
    ]:
        if os.path.isfile(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass


def test_self_hosting_driver_jit():
    """src/kale_self/main.kl: compile_source works directly via in-memory JIT"""
    from kale.diagnostics.source_text import SourceText
    from kale.diagnostics.diagnostic_bag import DiagnosticBag
    from kale.parser.parser import Parser
    from kale.binding.binder import Binder
    from kale.binding.module_loader import ModuleLoader
    from kale.codegen.llvm_emitter import LLVMEmitter
    from kale.codegen.llvm_jit import LLVMJIT

    code = """
    import "src/kale_self/main.kl" as km;
    extern void* strstr(string haystack, string needle);

    string src = "fn int multiply(int a, int b) { return a * b; } fn int main() { return multiply(6, 7); }";
    string c_code = km.compile_source(src);

    if ((void*)c_code == (void*)0) {
        return 1;
    }
    if (strstr(c_code, "multiply") == (void*)0) {
        return 2;
    }
    return 42;
    """

    st = SourceText(code)
    diag = DiagnosticBag()
    loader = ModuleLoader([os.path.abspath(".")], diag)
    parser = Parser(st, diag)
    unit = parser.parse_compilation_unit()
    assert not diag.has_errors, f"Parser errors: {[d.message for d in diag]}"

    binder = Binder(diag, module_loader=loader)
    bound = binder.bind_program(unit)
    assert not diag.has_errors, f"Binder errors: {[d.message for d in diag]}"

    emitter = LLVMEmitter()
    llvm_mod = emitter.emit_module(bound)
    jit = LLVMJIT()
    ret = jit.run_ir(str(llvm_mod))
    assert ret == 42
