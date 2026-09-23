"""Multi-configuration automated matrix test runner with JUnit XML reporting."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def run_test_matrix(suite_dir: str = "tests", xml_out: str | None = None) -> int:
    matrix_configs = [
        {"name": "Debug (unoptimized)", "flags": ["--ignore=tests/test_editor_command_bar.py", "-k", "not slow"]},
        {"name": "Fast Units", "flags": ["tests/test_lexer.py", "tests/test_parser.py", "tests/test_binder.py"]},
        {"name": "Codegen & Driver", "flags": ["tests/test_codegen.py", "tests/test_llvm_driver.py"]},
    ]

    print(f"\033[1;34m[kale test-matrix]\033[0m Starting matrix test runner ({len(matrix_configs)} configurations)...")
    results = []

    overall_start = time.perf_counter()

    for cfg in matrix_configs:
        c_name = cfg["name"]
        print(f"\n--> Running Matrix Target: \033[1;36m{c_name}\033[0m")
        cmd = ["uv", "run", "pytest", "-q"] + cfg["flags"]

        t0 = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        dur = time.perf_counter() - t0

        passed = proc.returncode == 0
        status_str = "\033[1;32mPASSED\033[0m" if passed else "\033[1;31mFAILED\033[0m"
        print(f"    Status: {status_str} in {dur:.2f}s")
        results.append((c_name, passed, dur))

    total_time = time.perf_counter() - overall_start

    print("\n" + "=" * 60)
    print(" KALE TEST MATRIX EXECUTION SUMMARY")
    print("=" * 60)
    print(f"{'CONFIGURATION':<36} {'RESULT':<12} {'DURATION':<10}")
    print("-" * 60)

    all_passed = True
    for name, passed, dur in results:
        res_tag = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"{name:<36} {res_tag:<12} {dur:.2f}s")

    print("-" * 60)
    print(f"Total Duration: {total_time:.2f}s")

    if xml_out:
        out_p = Path(xml_out)
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuites time="{total_time:.2f}">',
            f'  <testsuite name="kale-matrix" tests="{len(results)}">',
        ]
        for name, passed, dur in results:
            xml_lines.append(f'    <testcase classname="Matrix" name="{name}" time="{dur:.2f}">')
            if not passed:
                xml_lines.append('      <failure message="Matrix target test failed"/>')
            xml_lines.append('    </testcase>')
        xml_lines.extend(['  </testsuite>', '</testsuites>'])
        out_p.write_text("\n".join(xml_lines), encoding="utf-8")
        print(f"Wrote JUnit XML report to '{xml_out}'.")

    return 0 if all_passed else 1
