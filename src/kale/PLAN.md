# PythonKale Compiler Stabilization Plan (`src/kale`)

## 1. Executive Summary
The PythonKale compiler is the primary bootstrapping toolchain for the Kale language. Before complex graphics, networking, and self-hosting can occur, the compiler must be hardened, supporting IEEE 754 floating-point numbers, arbitrary C library linker flags, and struct value semantics.

---

## 2. Planned Architecture Enhancements

### 2.1 Floating Point Primitives (`f32`, `f64`)
- **Binding Phase (`src/kale/binding/types.py`)**:
  - Add `TypeFloat32` (`f32`, `float32`) and `TypeFloat64` (`f64`, `float64`).
  - Add implicit type coercion rules (e.g. `int` to `float64`, `f32` to `f64`).
- **Codegen Phase (`src/kale/codegen/llvm_types.py` & `llvm_emitter.py`)**:
  - Map `TypeFloat32` to `ir.FloatType()`, `TypeFloat64` to `ir.DoubleType()`.
  - Emit floating point operations: `fadd`, `fsub`, `fmul`, `fdiv`, `fcmp_ordered`.
  - Support float literals (`3.14159f`, `0.0`).

### 2.2 Dynamic Linker Passthrough (`-l`, `-L`)
- **CLI & Driver (`src/kale/cli.py` & `src/kale/codegen/compiler.py`)**:
  - Add command line flags: `-l <library>` (e.g. `-lglfw3`, `-lopengl32`, `-lws2_32`).
  - Add library search directories: `-L <directory>`.
  - Pass these arguments down to the Clang/LLD linker execution string.

### 2.3 Struct-by-Value Semantics
- **Codegen (`src/kale/codegen/llvm_emitter.py`)**:
  - Implement struct value returns from functions (allocating stack slot in caller frame and passing sret or returning first-class aggregate).
  - Ensure struct assignments load the aggregate value rather than treating pointer addresses as integers.

### 2.4 Stack Array Allocation
- Support array literal syntax `let items = [10, 20, 30];` allocated on the stack via `alloca`.

---

## 3. Implementation Milestones

- [ ] **Phase 1: Float Types**: Implement `f32` and `f64` in lexer, parser, binder, and LLVM emitter.
- [ ] **Phase 2: Linker Flags**: Expose `-l` and `-L` flags in `kale build` CLI.
- [ ] **Phase 3: Struct Value Returns**: Fix function return handling for geometric structs (`Point`, `Rect`, `Vec2`).
- [ ] **Phase 4: Comprehensive Test Suite**: Add tests in `tests/test_floats.py` and `tests/test_linker_args.py`.
