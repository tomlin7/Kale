# Bootstrap Benchmark Suite

## Objective
Evaluate the compilation performance of **PythonKale** vs **ZigKale** when compiling the complete self-hosting compiler codebase (`src/kale_self/main.kl`).

`src/kale_self/main.kl` represents the largest monolithic compilation target in the Kale codebase, exercising:
- Tokenizer & Lexer (`token.kl`, `lexer.kl`)
- Abstract Syntax Tree (`ast.kl`)
- Recursive Descent Parser (`parser.kl`)
- Semantic Type Checker (`checker.kl`)
- C Code Emitter (`codegen.kl`)
- Standard File I/O and CLI Driver

---

## Execution
```powershell
uv run python bench/suites/bootstrap/bench_bootstrap.py [--runs N] [--verbose]
```

## Tracked Metrics
1. **Compilation Time (ms)**: Time taken to compile `src/kale_self/main.kl` into native executable.
2. **Output Binary Size (KB)**: Size of the produced `kalec` executable.
3. **Execution Verification**: Ensures produced binary executes correctly against the test harness.
