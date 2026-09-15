# Microbenchmark Suite

## Objective
Evaluate compilation speed and runtime execution performance across core Kale computational primitives:

1. **Recursion (`recursion.kl`)**: Deep call stacks (Factorial of 20, Fibonacci calculations).
2. **Array Operations (`arrays.kl`)**: Heap/stack array indexing, in-place mutations, accumulation loops.
3. **Pointers & Memory (`pointers.kl`)**: Dynamic `alloc()`/`free()`, address-of (`&`), and pointer dereferences (`*`).

---

## Execution
```powershell
uv run python bench/suites/micro/bench_micro.py [--runs N]
```
