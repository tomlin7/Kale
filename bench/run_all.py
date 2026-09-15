import os
import sys
import subprocess
import argparse

BENCH_DIR = os.path.abspath(os.path.dirname(__file__))

def main():
    parser = argparse.ArgumentParser(description="Run all Kale benchmark suites")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark iterations (default: 3)")
    args = parser.parse_args()

    print("=================================================================")
    print("           KALE ECOSYSTEM UNIVERSAL BENCHMARK RUNNER")
    print("=================================================================\n")

    bootstrap_script = os.path.join(BENCH_DIR, "suites", "bootstrap", "bench_bootstrap.py")
    micro_script = os.path.join(BENCH_DIR, "suites", "micro", "bench_micro.py")

    if os.path.isfile(bootstrap_script):
        subprocess.run([sys.executable, bootstrap_script, "--runs", str(args.runs)], check=True)

    if os.path.isfile(micro_script):
        subprocess.run([sys.executable, micro_script, "--runs", str(args.runs)], check=True)

    print("All benchmark suites completed successfully.")

if __name__ == "__main__":
    main()
