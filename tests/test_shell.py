import subprocess, sys

def test_term_shell_executor():
    """libs/term/shell: command executor bridge bound to terminal grid"""
    r = subprocess.run(
        ["uv", "run", "--directory", "E:/kale", "python", "-m", "kale.cli", "build",
         "tests/test_shell.kl", "-o", "bin/test_shell.exe"],
        capture_output=True, text=True, cwd="E:/kale"
    )
    assert r.returncode == 0, f"Compile failed:\n{r.stdout}\n{r.stderr}"

    r2 = subprocess.run(["bin/test_shell.exe"], capture_output=True, text=True, cwd="E:/kale")
    assert r2.returncode == 0, f"Runtime failed: code {r2.returncode}\n{r2.stdout}"
    assert "ALL LIBS/TERM/SHELL TESTS PASSED PERFECTLY." in r2.stdout
