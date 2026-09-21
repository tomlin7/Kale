"""
src/kale/tools/test_runner.py
Parallel test runner for Kale (.kl) test suites.
Discovers tests, executes them via JIT or compilation, and reports test results.
"""

import os
import sys
import time
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict

class TestResult:
    def __init__(self, file_path: str, passed: bool, duration_ms: float, stdout: str, stderr: str):
        self.file_path = file_path
        self.passed = passed
        self.duration_ms = duration_ms
        self.stdout = stdout
        self.stderr = stderr


def run_single_test(test_file: str) -> TestResult:
    t0 = time.perf_counter()
    cmd = [sys.executable, "-m", "kale", "run", test_file]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    t1 = time.perf_counter()

    duration_ms = (t1 - t0) * 1000.0
    passed = (res.returncode == 0)
    return TestResult(test_file, passed, duration_ms, res.stdout, res.stderr)


def discover_tests(targets: List[str], pattern: str | None = None) -> List[str]:
    test_files: List[str] = []
    for t in targets:
        if os.path.isfile(t) and t.endswith(".kl"):
            test_files.append(t)
        elif os.path.isdir(t):
            for root, _, files in os.walk(t):
                for f in files:
                    if f.endswith(".kl"):
                        if f.startswith("test_") or f.endswith("_test.kl") or "tests" in root.replace("\\", "/").split("/"):
                            test_files.append(os.path.join(root, f))

    if pattern:
        test_files = [f for f in test_files if pattern in os.path.basename(f)]

    return sorted(test_files)


def run_tests(targets: List[str], jobs: int = 4, pattern: str | None = None) -> int:
    test_files = discover_tests(targets, pattern=pattern)

    if not test_files:
        print("No test files found.")
        return 0

    print(f"Running {len(test_files)} test(s) using {jobs} worker(s)...\n")

    results: List[TestResult] = []
    passed_count = 0
    failed_count = 0

    t_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        future_to_test = {executor.submit(run_single_test, tf): tf for tf in test_files}
        for future in as_completed(future_to_test):
            res = future.result()
            results.append(res)
            rel_name = os.path.relpath(res.file_path, ".")
            if res.passed:
                passed_count += 1
                print(f"  \033[92m[PASS]\033[0m {rel_name:<45} ({res.duration_ms:.1f}ms)")
            else:
                failed_count += 1
                print(f"  \033[91m[FAIL]\033[0m {rel_name:<45} ({res.duration_ms:.1f}ms)")
                if res.stderr:
                    for line in res.stderr.strip().splitlines():
                        print(f"         {line}")

    t_total = time.perf_counter() - t_start

    print("\n" + "─" * 60)
    print(f"Test Summary: {passed_count} passed, {failed_count} failed, {len(test_files)} total in {t_total:.2f}s")
    print("─" * 60)

    return 1 if failed_count > 0 else 0
