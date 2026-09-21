# tools/bench — kale bench

Statistical micro-benchmarking harness for Kale.

## Features

- **Warmup Phase**: Eliminates cold-cache / page fault noise.
- **High-Resolution Timing**: Measures down to nanoseconds using `time.perf_counter_ns()`.
- **Statistical Breakdown**: Calculates Mean, Median, Min, Max, Standard Deviation, and Ops/sec.
- **Auto-Discovery**: Scans directories for `bench_*.kl` files.

## Usage

```bash
python tools/bench/bench.py <path_or_dir> [-w WARMUP] [-n ITERATIONS] [-O OPT_LEVEL]
```
