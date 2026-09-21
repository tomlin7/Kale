"""
tools/bench/bench.py
Statistical micro-benchmarking harness for Kale.

Measures execution time across multiple iterations with warmup cycles,
calculating Mean, Median, Standard Deviation, Min, Max, and Ops/sec.
"""

import sys
import os
import time
import math
import argparse
import subprocess
from typing import List, Dict, Any

class BenchmarkResult:
    def __init__(self, name: str, runs: List[float]):
        self.name = name
        self.runs = runs  # in nanoseconds
        self.count = len(runs)

        if runs:
            self.min_ns = min(runs)
            self.max_ns = max(runs)
            self.mean_ns = sum(runs) / self.count
            sorted_runs = sorted(runs)
            mid = self.count // 2
            if self.count % 2 == 0:
                self.median_ns = (sorted_runs[mid - 1] + sorted_runs[mid]) / 2.0
            else:
                self.median_ns = sorted_runs[mid]

            variance = sum((x - self.mean_ns) ** 2 for x in runs) / max(1, self.count - 1)
            self.stddev_ns = math.sqrt(variance)
        else:
            self.min_ns = self.max_ns = self.mean_ns = self.median_ns = self.stddev_ns = 0.0

    def format_time(self, ns: float) -> str:
        if ns < 1000:
            return f"{ns:.1f} ns"
        elif ns < 1_000_000:
            return f"{ns / 1000:.2f} µs"
        elif ns < 1_000_000_000:
            return f"{ns / 1_000_000:.2f} ms"
        else:
            return f"{ns / 1_000_000_000:.2f} s"

    def ops_per_sec(self) -> float:
        if self.mean_ns > 0:
            return 1_000_000_000.0 / self.mean_ns
        return 0.0


def run_benchmark_target(target_path: str, warmup: int = 3, iterations: int = 10, opt: int = 3) -> BenchmarkResult:
    name = os.path.splitext(os.path.basename(target_path))[0]
    print(f"Running benchmark: {name} ({iterations} iterations, {warmup} warmup)...")

    # Compile the benchmark file once to an executable using kale CLI
    exe_path = os.path.splitext(target_path)[0] + ("_bench.exe" if os.name == "nt" else "_bench")
    cmd_build = [sys.executable, "-m", "kale", "build", target_path, "-o", exe_path, f"-O{opt}"]
    res = subprocess.run(cmd_build, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Build failed for {target_path}:\n{res.stderr}")
        return BenchmarkResult(name, [])

    # Warmup
    for _ in range(warmup):
        subprocess.run([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Measure
    runs: List[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        subprocess.run([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t1 = time.perf_counter_ns()
        runs.append(float(t1 - t0))

    # Clean up executable
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
        except Exception:
            pass

    return BenchmarkResult(name, runs)


def print_table(results: List[BenchmarkResult]):
    header = f"{'Benchmark':<25} {'Mean':<14} {'Median':<14} {'Min':<14} {'Max':<14} {'StdDev':<12} {'Ops/sec':<12}"
    divider = "─" * len(header)
    print("\n" + divider)
    print(header)
    print(divider)

    for r in results:
        if r.count == 0:
            print(f"{r.name:<25} {'FAILED':<14}")
            continue
        print(
            f"{r.name:<25} "
            f"{r.format_time(r.mean_ns):<14} "
            f"{r.format_time(r.median_ns):<14} "
            f"{r.format_time(r.min_ns):<14} "
            f"{r.format_time(r.max_ns):<14} "
            f"±{r.format_time(r.stddev_ns):<11} "
            f"{r.ops_per_sec():>10.1f}"
        )
    print(divider + "\n")


def main():
    parser = argparse.ArgumentParser(description="Kale Statistical Micro-Benchmarking Harness")
    parser.add_argument("targets", nargs="+", help="Paths to .kl benchmark files or directories")
    parser.add_argument("-w", "--warmup", type=int, default=3, help="Warmup iterations (default: 3)")
    parser.add_argument("-n", "--iterations", type=int, default=10, help="Measurement iterations (default: 10)")
    parser.add_argument("-O", "--opt", type=int, default=3, help="Optimization level (default: 3)")

    args = parser.parse_args()

    bench_files: List[str] = []
    for t in args.targets:
        if os.path.isfile(t) and t.endswith(".kl"):
            bench_files.append(t)
        elif os.path.isdir(t):
            for root, _, files in os.walk(t):
                for f in files:
                    if f.startswith("bench_") and f.endswith(".kl"):
                        bench_files.append(os.path.join(root, f))

    if not bench_files:
        print("No benchmark files found. File names should start with 'bench_' and end with '.kl'")
        sys.exit(1)

    results: List[BenchmarkResult] = []
    for bf in bench_files:
        res = run_benchmark_target(bf, warmup=args.warmup, iterations=args.iterations, opt=args.opt)
        results.append(res)

    print_table(results)


if __name__ == "__main__":
    main()
