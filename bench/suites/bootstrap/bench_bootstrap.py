import os
import sys
import time
import subprocess
import argparse
import shutil
import statistics

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TARGET_KL = os.path.join(REPO_ROOT, "src", "kale_self", "main.kl")
BIN_DIR = os.path.join(REPO_ROOT, "bin")

EXE_SUFFIX = ".exe" if os.name == "nt" else ""
ZIGKALE_EXE = os.path.join(REPO_ROOT, "src", "zigkale", "zig-out", "bin", f"zigkale{EXE_SUFFIX}")

def ensure_bin_dir():
    os.makedirs(BIN_DIR, exist_ok=True)

def ensure_zigkale_built():
    if not os.path.isfile(ZIGKALE_EXE):
        print("[bench] Building ZigKale compiler...")
        subprocess.run(["zig", "build"], cwd=os.path.join(REPO_ROOT, "src", "zigkale"), check=True)

def time_command(cmd, cwd=REPO_ROOT):
    start = time.perf_counter()
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if res.returncode != 0:
        raise RuntimeError(f"Command failed (code {res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return elapsed_ms

def benchmark_compiler(name, build_fn, runs):
    print(f"\n--- Benchmarking {name} ({runs} runs) ---")
    times = []
    # Warmup
    print(f"  Warmup pass...", end="", flush=True)
    build_fn()
    print(" done.")
    
    for i in range(1, runs + 1):
        print(f"  Run {i}/{runs}...", end="", flush=True)
        ms = build_fn()
        times.append(ms)
        print(f" {ms:.1f} ms")
        
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0.0
    fastest = min(times)
    slowest = max(times)
    print(f"  Result: Mean = {mean:.1f} ms | Min = {fastest:.1f} ms | Max = {slowest:.1f} ms | StdDev = {stdev:.1f} ms")
    return {
        "name": name,
        "runs": times,
        "mean": mean,
        "min": fastest,
        "max": slowest,
        "stdev": stdev
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark PythonKale vs ZigKale bootstrapping src/kale_self/main.kl")
    parser.add_argument("--runs", type=int, default=5, help="Number of benchmark iterations (default: 5)")
    args = parser.parse_args()

    ensure_bin_dir()
    ensure_zigkale_built()

    out_py = os.path.join(BIN_DIR, f"bench_kalec_py{EXE_SUFFIX}")
    out_zig = os.path.join(BIN_DIR, f"bench_kalec_zig{EXE_SUFFIX}")

    # PythonKale build function
    def build_pythonkale():
        cmd = ["uv", "run", "--directory", REPO_ROOT, "python", "-m", "kale.cli", "build", TARGET_KL, "-o", out_py]
        return time_command(cmd)

    # ZigKale build function
    def build_zigkale():
        cmd = [ZIGKALE_EXE, "build", TARGET_KL, "-o", out_zig]
        return time_command(cmd)

    print("=================================================================")
    print("  KALE BOOTSTRAP COMPILATION BENCHMARK")
    print(f"  Target: {os.path.relpath(TARGET_KL, REPO_ROOT)}")
    print("=================================================================")

    py_stats = benchmark_compiler("PythonKale", build_pythonkale, args.runs)
    zig_stats = benchmark_compiler("ZigKale", build_zigkale, args.runs)

    # Measure binary sizes
    size_py = os.path.getsize(out_py) if os.path.isfile(out_py) else 0
    size_zig = os.path.getsize(out_zig) if os.path.isfile(out_zig) else 0

    # Measure execution latency of both produced compilers (--help)
    def test_invoke(exe):
        times = []
        for _ in range(10):
            t = time_command([exe, "--help"])
            times.append(t)
        return statistics.mean(times)

    invoke_py = test_invoke(out_py)
    invoke_zig = test_invoke(out_zig)

    speedup_mean = py_stats["mean"] / zig_stats["mean"] if zig_stats["mean"] > 0 else 0
    speedup_warm = py_stats["min"] / zig_stats["min"] if zig_stats["min"] > 0 else 0

    print("\n=================================================================")
    print("  SUMMARY COMPARISON")
    print("=================================================================")
    print(f"  PythonKale Compile Mean:  {py_stats['mean']:.1f} ms  (Min: {py_stats['min']:.1f} ms)")
    print(f"  ZigKale Compile Mean:     {zig_stats['mean']:.1f} ms  (Min: {zig_stats['min']:.1f} ms)")
    print(f"  Compilation Speedup:      {speedup_mean:.2f}x faster overall ({speedup_warm:.2f}x on warm runs)")
    print("-----------------------------------------------------------------")
    print(f"  kalec_py Size:            {size_py:,} bytes ({size_py/1024:.1f} KB)")
    print(f"  kalec_zig Size:           {size_zig:,} bytes ({size_zig/1024:.1f} KB)")
    print(f"  kalec_py Launch Latency:  {invoke_py:.2f} ms")
    print(f"  kalec_zig Launch Latency: {invoke_zig:.2f} ms")
    print("=================================================================\n")

if __name__ == "__main__":
    main()
