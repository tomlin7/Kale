import subprocess, sys

def test_matrix_linear_algebra():
    """packages/std/math: Vec2, Vec3, Mat3 operations"""
    r = subprocess.run(
        ["uv", "run", "--directory", "E:/kale", "python", "-m", "kale.cli", "build",
         "tests/test_matrix.kl", "-o", "bin/test_matrix.exe"],
        capture_output=True, text=True, cwd="E:/kale"
    )
    assert r.returncode == 0, f"Compile failed:\n{r.stdout}\n{r.stderr}"

    r2 = subprocess.run(["bin/test_matrix.exe"], capture_output=True, text=True, cwd="E:/kale")
    assert r2.returncode == 0, f"Runtime failed: code {r2.returncode}\n{r2.stdout}"
    assert "ALL PACKAGES/STD/MATH TESTS PASSED PERFECTLY." in r2.stdout
