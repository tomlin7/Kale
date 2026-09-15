import subprocess

def test_json_builder():
    """libs/json: JsonValue, JsonObject, JsonArray builders"""
    r = subprocess.run(
        ["uv", "run", "--directory", "E:/kale", "python", "-m", "kale.cli", "build",
         "tests/test_json.kl", "-o", "bin/test_json.exe"],
        capture_output=True, text=True, cwd="E:/kale"
    )
    assert r.returncode == 0, f"Compile failed:\n{r.stdout}\n{r.stderr}"
    r2 = subprocess.run(["bin/test_json.exe"], capture_output=True, text=True, cwd="E:/kale")
    assert r2.returncode == 0, f"Runtime failed: code {r2.returncode}\n{r2.stdout}"
    assert "ALL LIBS/JSON TESTS PASSED PERFECTLY." in r2.stdout
