import os
import sys
import time
import subprocess
import argparse
import statistics

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples")
BIN_DIR = os.path.join(REPO_ROOT, "bin")

EXE_SUFFIX = ".exe" if os.name == "nt" else ""
ZIGKALE_EXE = os.path.join(REPO_ROOT, "src", "zigkale", "zig-out", "bin", f"zigkale{EXE_SUFFIX}")

TARGETS = [
    ("recursion", os.path.join(EXAMPLES_DIR, "recursion.kl")),
    ("arrays", os.path.join(EXAMPLES_DIR, "arrays.kl")),
    ("pointers", os.path.join(EXAMPLES_DIR, "pointers.kl")),
]

def ensure_bin_dir():
    os.makedirs(BIN_DIR, exist_ok=True)

def ensure_zigkale_built():
    if not os.path.isfile(ZIGKALE_EXE):
        subprocess.run(["zig", "build"], cwd=os.path.join(REPO_ROOT, "src", "zigkale"), check=True)

def time_command(cmd, cwd=REPO_ROOT):
    start = time.perf_counter()
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if res.returncode != 0:
        raise RuntimeError(f"Command failed (code {res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return elapsed_ms

def run_micro_suite(runs):
    ensure_bin_dir()
    ensure_zigkale_built()

    print("=================================================================")
    print("  KALE MICROBENCHMARK SUITE")
    print("=================================================================")

    for name, kl_file in TARGETS:
        if not os.path.isfile(kl_file):
            continue
        print(f"\n--- Target: {name}.kl ---")

        out_py = os.path.join(BIN_DIR, f"bench_{name}_py{EXE_SUFFIX}")
        out_zig = os.path.join(BIN_DIR, f"bench_{name}_zig{EXE_SUFFIX}")

        cmd_py = ["uv", "run", "--directory", REPO_ROOT, "python", "-m", "kale.cli", "build", kl_file, "-o", out_py]
        cmd_zig = [ZIGKALE_EXE, "build", kl_file, "-o", out_zig]

        # Warmup
        time_command(cmd_py)
        time_command(cmd_zig)

        py_compile_times = []
        zig_compile_times = []
        for _ in range(runs):
            py_compile_times.append(time_command(cmd_py))
            zig_compile_times.append(time_command(cmd_zig))

        py_run_times = []
        zig_run_times = []
        for _ in range(runs):
            py_run_times.append(time_command([out_py]))
            zig_run_times.append(time_command([out_zig]))

        mean_py_comp = statistics.mean(py_compile_times)
        mean_zig_comp = statistics.mean(zig_compile_times)
        speedup = mean_py_comp / mean_zig_comp if mean_zig_comp > 0 else 0

        mean_py_exec = statistics.mean(py_run_times)
        mean_zig_exec = statistics.mean(zig_run_times)

        print(f"  Compile Time: PythonKale = {mean_py_comp:.1f} ms | ZigKale = {mean_zig_comp:.1f} ms (Speedup: {speedup:.2f}x)")
        print(f"  Exec Time:    Python-built = {mean_py_exec:.2f} ms | Zig-built = {mean_zig_exec:.2f} ms")

    print("\n=================================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Run Kale microbenchmark suite")
    parser.add_argument("--runs", type=int, default=5, help="Number of iterations (default: 5)")
    args = parser.parse_args()
    run_micro_suite(args.runs)

if __name__ == "__main__":
    main()
