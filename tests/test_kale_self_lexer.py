import subprocess, sys

def test_self_hosting_lexer():
    """src/kale_self: Kale self-hosting lexer tokenizes correctly"""
    r = subprocess.run(
        ["uv", "run", "--directory", "E:/kale", "python", "-m", "kale.cli", "build",
         "tests/test_kale_self_lexer.kl", "-o", "bin/test_kale_self_lexer.exe"],
        capture_output=True, text=True, cwd="E:/kale"
    )
    assert r.returncode == 0, f"Compile failed:\n{r.stdout}\n{r.stderr}"

    r2 = subprocess.run(["bin/test_kale_self_lexer.exe"], capture_output=True, text=True, cwd="E:/kale")
    assert r2.returncode == 0, f"Runtime failed: code {r2.returncode}\n{r2.stdout}"
    assert "ALL SELF-HOSTING LEXER TESTS PASSED PERFECTLY." in r2.stdout
