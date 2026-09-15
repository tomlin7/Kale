import subprocess
import os
import shutil
import pytest

EXE_NAME = "zigkale.exe" if os.name == "nt" else "zigkale"
ZIGKALE_EXE = os.path.abspath(os.path.join("src/zigkale/zig-out/bin", EXE_NAME))
HAS_ZIG = shutil.which("zig") is not None

def ensure_zigkale_built():
    if not os.path.isfile(ZIGKALE_EXE):
        subprocess.run(["zig", "build"], cwd="src/zigkale", check=True)

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_version_and_help():
    ensure_zigkale_built()
    r = subprocess.run([ZIGKALE_EXE, "--version"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "ZigKale v0.1.0" in (r.stdout + r.stderr)

    r2 = subprocess.run([ZIGKALE_EXE, "--help"], capture_output=True, text=True)
    assert r2.returncode == 0
    assert "Usage: zigkale" in (r2.stdout + r2.stderr)

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_build_and_run_simple():
    ensure_zigkale_built()
    os.makedirs("bin", exist_ok=True)
    ext = ".exe" if os.name == "nt" else ""
    exe_path = os.path.abspath(f"bin/test_simple_zig{ext}")
    src_path = os.path.abspath("src/kale/hello.kl")

    try:
        r = subprocess.run(
            [ZIGKALE_EXE, "build", src_path, "-o", exe_path],
            capture_output=True, text=True
        )
        assert r.returncode == 0, f"ZigKale build failed:\n{r.stdout}\n{r.stderr}"
        assert os.path.isfile(exe_path)

        r2 = subprocess.run([exe_path], capture_output=True, text=True)
        assert r2.returncode == 0
    finally:
        if os.path.isfile(exe_path):
            try:
                os.remove(exe_path)
            except OSError:
                pass

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_build_and_run_examples():
    """Verify ZigKale compiles and runs arrays, hello string variable, and recursion."""
    ensure_zigkale_built()
    os.makedirs("bin", exist_ok=True)
    ext = ".exe" if os.name == "nt" else ""

    # Test 1: examples/hello.kl (verifies string variable print and _kale_print_str)
    hello_exe = os.path.abspath(f"bin/test_hello_zig{ext}")
    try:
        r = subprocess.run([ZIGKALE_EXE, "build", "examples/hello.kl", "-o", hello_exe], capture_output=True, text=True)
        assert r.returncode == 0, f"hello.kl build failed: {r.stderr}"
        r_run = subprocess.run([hello_exe], capture_output=True, text=True)
        assert r_run.returncode == 0
        assert "Hello, Kale World!" in r_run.stdout
    finally:
        if os.path.isfile(hello_exe):
            try: os.remove(hello_exe)
            except OSError: pass

    # Test 2: examples/arrays.kl (verifies array declaration, indexing, assignment, loops)
    arrays_exe = os.path.abspath(f"bin/test_arrays_zig{ext}")
    try:
        r = subprocess.run([ZIGKALE_EXE, "build", "examples/arrays.kl", "-o", arrays_exe], capture_output=True, text=True)
        assert r.returncode == 0, f"arrays.kl build failed: {r.stderr}"
        r_run = subprocess.run([arrays_exe], capture_output=True, text=True)
        assert r_run.returncode == 0
        assert "Sum of array elements: 1119" in r_run.stdout
    finally:
        if os.path.isfile(arrays_exe):
            try: os.remove(arrays_exe)
            except OSError: pass

    # Test 3: examples/recursion.kl (verifies recursive functions)
    rec_exe = os.path.abspath(f"bin/test_recursion_zig{ext}")
    try:
        r = subprocess.run([ZIGKALE_EXE, "build", "examples/recursion.kl", "-o", rec_exe], capture_output=True, text=True)
        assert r.returncode == 0, f"recursion.kl build failed: {r.stderr}"
        r_run = subprocess.run([rec_exe], capture_output=True, text=True)
        assert r_run.returncode == 0
        assert "Factorial of 5 is: 120" in r_run.stdout
        assert "Fibonacci(10) is: 55" in r_run.stdout
    finally:
        if os.path.isfile(rec_exe):
            try: os.remove(rec_exe)
            except OSError: pass

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_bootstrap_compiler():
    ensure_zigkale_built()
    os.makedirs("bin", exist_ok=True)
    ext = ".exe" if os.name == "nt" else ""
    exe_path = os.path.abspath(f"bin/kalec_zig{ext}")
    src_path = os.path.abspath("src/kale_self/main.kl")

    r = subprocess.run(
        [ZIGKALE_EXE, "build", src_path, "-o", exe_path],
        capture_output=True, text=True
    )
    assert r.returncode == 0, f"ZigKale bootstrap build failed:\n{r.stdout}\n{r.stderr}"
    assert os.path.isfile(exe_path)

    r2 = subprocess.run([exe_path], capture_output=True, text=True)
    assert r2.returncode == 0
    assert "Kale Self-Hosting Compiler (kalec v0.1.0)" in r2.stdout
    assert "Usage: kalec <input.kl>" in r2.stdout

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_unit_tests():
    r = subprocess.run(["zig", "build", "test"], cwd="src/zigkale", capture_output=True, text=True)
    assert r.returncode == 0, f"ZigKale unit tests failed:\n{r.stdout}\n{r.stderr}"
