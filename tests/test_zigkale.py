import subprocess
import os
import shutil
import pytest

ZIGKALE_EXE = os.path.abspath("src/zigkale/zig-out/bin/zigkale.exe")

def ensure_zigkale_built():
    if not os.path.isfile(ZIGKALE_EXE):
        subprocess.run(["zig", "build"], cwd="src/zigkale", check=True)

def test_zigkale_version_and_help():
    ensure_zigkale_built()
    r = subprocess.run([ZIGKALE_EXE, "--version"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "ZigKale v0.1.0" in (r.stdout + r.stderr)

    r2 = subprocess.run([ZIGKALE_EXE, "--help"], capture_output=True, text=True)
    assert r2.returncode == 0
    assert "Usage: zigkale" in (r2.stdout + r2.stderr)

def test_zigkale_build_and_run_simple():
    ensure_zigkale_built()
    os.makedirs("bin", exist_ok=True)
    exe_path = os.path.abspath("bin/test_simple_zig.exe")
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

def test_zigkale_bootstrap_compiler():
    ensure_zigkale_built()
    os.makedirs("bin", exist_ok=True)
    exe_path = os.path.abspath("bin/kalec_zig.exe")
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

def test_zigkale_unit_tests():
    r = subprocess.run(["zig", "build", "test"], cwd="src/zigkale", capture_output=True, text=True)
    assert r.returncode == 0, f"ZigKale unit tests failed:\n{r.stdout}\n{r.stderr}"
