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

def _run_zigkale_snippet(tmp_path, code: str) -> subprocess.CompletedProcess:
    ensure_zigkale_built()
    src_file = tmp_path / "test_snippet.kl"
    exe_file = tmp_path / ("test_snippet.exe" if os.name == "nt" else "test_snippet")
    src_file.write_text(code, encoding="utf-8")

    build_res = subprocess.run(
        [ZIGKALE_EXE, "build", str(src_file), "-o", str(exe_file)],
        capture_output=True, text=True
    )
    assert build_res.returncode == 0, f"Build failed:\nStdout: {build_res.stdout}\nStderr: {build_res.stderr}"
    assert exe_file.is_file()

    return subprocess.run([str(exe_file)], capture_output=True, text=True)

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_bitwise_and_casts(tmp_path):
    code = """
    int a = 10 & 12;
    int b = 10 | 5;
    int c = 10 ^ 12;
    int d = 1 << 4;
    int e = 32 >> 2;
    int f = (~0) & 255;
    int sum = a + b + c + d + e + f;
    print(sum); // 308

    int x = 1;
    x <<= 3;
    x |= 2;
    x &= 14;
    x ^= 3;
    x >>= 1;
    print(x); // 4

    double pi = 3.14159;
    int int_pi = (int)pi;
    int truncated = pi as int;
    char ch = 65 as char;
    print(int_pi, truncated, ch); // 3 3 65

    int* p = alloc(int, 2);
    p[0] = 42;
    p[1] = 99;
    char* byte_ptr = p as char*;
    byte_ptr[0] = 7 as char;
    int res = p[0];
    print(res); // 7
    free(p);
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    lines = run_res.stdout.strip().splitlines()
    assert lines[0] == "308"
    assert lines[1] == "4"
    assert "3 3" in lines[2]
    assert lines[3] == "7"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_enums_and_switch(tmp_path):
    code = """
    enum Color {
        Red,
        Green = 5,
        Blue
    }

    Color c = Color.Green;
    print(Color.Red, Color.Green, Color.Blue);

    int evaluate(int val) {
        int result = 0;
        switch (val) {
            case 10:
                result = 100;
                break;
            case 20:
                result = 200;
                break;
            default:
                result = 300;
                break;
        }
        return result;
    }

    int handle_color(Color col) {
        int code = 0;
        switch (col) {
            case Color.Red:
                code = 10;
                break;
            case Color.Green:
                code = 20;
                break;
            case Color.Blue:
                code = 30;
                break;
            default:
                code = 99;
                break;
        }
        return code;
    }

    print(evaluate(10), evaluate(20), evaluate(99));
    print(handle_color(Color.Red), handle_color(Color.Green), handle_color(Color.Blue));
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    lines = run_res.stdout.strip().splitlines()
    assert lines[0] == "0 5 6"
    assert lines[1] == "100 200 300"
    assert lines[2] == "10 20 30"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_control_flow(tmp_path):
    code = """
    int sum = 0;
    for (int i = 0; i < 10; i++) {
        if (i == 3) {
            continue;
        }
        if (i == 7) {
            break;
        }
        sum += i;
    }
    print(sum); // 0 + 1 + 2 + 4 + 5 + 6 = 18
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    assert run_res.stdout.strip() == "18"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_function_pointers(tmp_path):
    code = """
    int add(int a, int b) {
        return a + b;
    }

    int sub(int a, int b) {
        return a - b;
    }

    int square(int x) {
        return x * x;
    }

    int apply(fn(int): int callback, int val) {
        return callback(val);
    }

    struct Button {
        int id;
        fn(int): int on_click;
    };

    fn(int, int): int op = add;
    int r1 = op(10, 20);

    op = sub;
    int r2 = op(50, 15);

    int r3 = apply(square, 9);

    Button btn;
    btn.id = 1;
    btn.on_click = square;
    int r4 = btn.on_click(5);

    print(r1, r2, r3, r4); // 30 35 81 25
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    assert run_res.stdout.strip() == "30 35 81 25"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_struct_methods(tmp_path):
    code = """
    struct Rectangle {
        int width;
        int height;
    };

    fn int Rectangle.area() {
        return this->width * this->height;
    }

    struct Counter {
        int count;
    };

    fn void Counter.increment(int delta) {
        this->count += delta;
    }

    fn int Counter.get() {
        return this->count;
    }

    struct Point {
        int x;
        int y;
    };

    fn void Point.set(int new_x, int new_y) {
        this->x = new_x;
        this->y = new_y;
    }

    fn int Point.sum() {
        return this->x + this->y;
    }

    Rectangle r;
    r.width = 5;
    r.height = 10;
    print(r.area()); // 50

    Counter c;
    c.count = 0;
    c.increment(5);
    c.increment(10);
    print(c.get()); // 15

    Point* p = alloc(Point);
    p->set(20, 30);
    print(p->sum()); // 50
    free(p);
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    lines = run_res.stdout.strip().splitlines()
    assert lines[0] == "50"
    assert lines[1] == "15"
    assert lines[2] == "50"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_global_variables(tmp_path):
    code = """
    int counter = 10;
    const int MULT = 5;

    fn void step() {
        counter += 2;
    }

    fn int compute() {
        return counter * MULT;
    }

    step();
    step();
    print(counter); // 14
    print(compute()); // 70
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    lines = run_res.stdout.strip().splitlines()
    assert lines[0] == "14"
    assert lines[1] == "70"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_multidimensional_and_nested(tmp_path):
    code = """
    struct Inner {
        int val;
    };

    struct Outer {
        Inner inner;
        int extra;
    };

    Outer out_obj;
    out_obj.inner.val = 42;
    out_obj.extra = 8;
    out_obj.inner.val += 10;
    print(out_obj.inner.val, out_obj.extra); // 52 8

    int* arr = alloc(int, 5);
    for (int i = 0; i < 5; i++) {
        arr[i] = i * 10;
    }
    arr[2] += 5;
    print(arr[0], arr[1], arr[2], arr[3], arr[4]); // 0 10 25 30 40
    free(arr);
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    lines = run_res.stdout.strip().splitlines()
    assert lines[0] == "52 8"
    assert lines[1] == "0 10 25 30 40"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_cli_tooling(tmp_path):
    ensure_zigkale_built()
    src_file = tmp_path / "hello_cli.kl"
    src_file.write_text('print("CLI check test");', encoding="utf-8")

    # 1. check mode
    r_check = subprocess.run([ZIGKALE_EXE, "check", str(src_file)], capture_output=True, text=True)
    assert r_check.returncode == 0
    assert "Check passed" in (r_check.stdout + r_check.stderr)

    # 2. dump-c mode
    r_dump = subprocess.run([ZIGKALE_EXE, "dump-c", str(src_file)], capture_output=True, text=True)
    assert r_dump.returncode == 0
    assert "#include <stdio.h>" in (r_dump.stdout + r_dump.stderr)

    # 3. --emit-c option
    exe_file = tmp_path / ("hello_cli.exe" if os.name == "nt" else "hello_cli")
    r_build = subprocess.run(
        [ZIGKALE_EXE, "build", str(src_file), "-o", str(exe_file), "--emit-c", "-I", str(tmp_path)],
        capture_output=True, text=True
    )
    assert r_build.returncode == 0
    c_file = tmp_path / "hello_cli.c"
    assert c_file.is_file(), f"Expected {c_file} to exist"

@pytest.mark.skipif(not HAS_ZIG, reason="zig not installed")
def test_zigkale_chained_method_calls(tmp_path):
    code = """
    struct Builder {
        int val;
    };

    fn Builder* Builder.add(int x) {
        this->val += x;
        return this;
    }

    fn int Builder.get() {
        return this->val;
    }

    Builder b;
    b.val = 10;
    b.add(5).add(20);
    print(b.get()); // 35
    """
    run_res = _run_zigkale_snippet(tmp_path, code)
    assert run_res.returncode == 0
    assert run_res.stdout.strip() == "35"

