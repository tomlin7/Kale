# Kale Ecosystem Benchmark Suite

This directory houses the performance and compilation benchmark suite for the **Kale Programming Language**. It tracks compilation throughput, runtime binary performance, and memory efficiency across the dual compiler implementations:

1. **PythonKale** (`src/kale/`) — Reference compiler written in Python with LLVM backend (`python -m kale.cli`).
2. **ZigKale** (`src/zigkale/`) — Native compiler written in Zig (`src/zigkale/zig-out/bin/zigkale`).
3. **Bootstrapped Compiler (`kalec`)** (`src/kale_self/`) — Self-hosting compiler written in pure Kale.

---

## Directory Layout

```text
bench/
├── README.md                      # This overview and benchmark methodology
├── run_all.py                     # Universal runner for all benchmark suites
└── suites/
    ├── bootstrap/                 # Self-hosting compiler bootstrap benchmarks
    │   ├── README.md              # Methodology and test target details
    │   └── bench_bootstrap.py     # Compiles src/kale_self/main.kl with both compilers
    └── micro/                     # Microbenchmarks (recursion, arrays, pointers)
        ├── README.md              # Language feature benchmarks
        └── bench_micro.py         # Comparative compile and execution time benchmarks
```

---

## Quick Start

### Run All Benchmarks
```powershell
uv run python bench/run_all.py
```

### Run Bootstrap Benchmark Only
```powershell
uv run python bench/suites/bootstrap/bench_bootstrap.py --runs 5
```

### Run Microbenchmark Suite Only
```powershell
uv run python bench/suites/micro/bench_micro.py --runs 5
```

---

## Benchmark Methodology

- **Warmup**: Each test runs at least 1 untimed warmup pass to eliminate file system cache bias.
- **Iterations**: Default is 5 timed iterations per compiler.
- **Metrics Tracked**:
  - **Compilation Throughput**: Time taken by the compiler to parse, type-check, and emit native machine code.
  - **Binary Size**: File size of the produced native executable in bytes.
  - **Runtime Execution**: Wall-clock duration of the compiled program executing its workload.
- **Environment**: Clean execution on host target machine without background interference.

---

## Latest Benchmark Results

### 1. Bootstrapping `src/kale_self/main.kl` (5 Runs)

| Compiler | Cold Run | Warm Min | Mean Latency | Speedup vs Python |
| :--- | :---: | :---: | :---: | :---: |
| **PythonKale** | 1,786.0 ms | 1,253.2 ms | 1,363.2 ms | 1.00x (baseline) |
| **ZigKale** | 1,081.7 ms | 222.3 ms | 396.9 ms | **3.43x (5.6x warm)** |

### 2. Resulting Compiler Binaries (`kalec`)

| Metric | `kalec_py.exe` (from PythonKale) | `kalec_zig.exe` (from ZigKale) |
| :--- | :---: | :---: |
| **Binary File Size** | 185,344 bytes (~181 KB) | 210,944 bytes (~206 KB) |
| **CLI Launch Latency** | ~12.29 ms | ~14.19 ms |
| **Self-Hosting Driver Tests** | 11 / 11 phases passed | 11 / 11 phases passed |
