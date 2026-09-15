import subprocess

def test_net_http_types():
    """libs/net/http: HttpResponse and ParsedUrl struct types"""
    r = subprocess.run(
        ["uv", "run", "--directory", "E:/kale", "python", "-m", "kale.cli", "build",
         "tests/test_net_http.kl", "-o", "bin/test_net_http.exe", "-l", "ws2_32"],
        capture_output=True, text=True, cwd="E:/kale"
    )
    assert r.returncode == 0, f"Compile failed:\n{r.stdout}\n{r.stderr}"
    r2 = subprocess.run(["bin/test_net_http.exe"], capture_output=True, text=True, cwd="E:/kale")
    assert r2.returncode == 0, f"Runtime failed: code {r2.returncode}\n{r2.stdout}"
    assert "ALL LIBS/NET/HTTP TESTS PASSED PERFECTLY." in r2.stdout
