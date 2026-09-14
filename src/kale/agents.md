# PythonKale Compiler

## Version
`0.2.0`

## Description
The reference Kale compiler implemented in Python. Lexes, parses, binds (type-checks), and emits LLVM IR. Compiles to native binaries via Clang/LLD. Also supports JIT execution.

## Status
Current status: 🟡 In Progress

## Dependencies
- Python 3.12+
- llvmlite
- uv package manager

## Build Instructions
- `uv sync` to install deps
- `uv run pytest` for tests
- `scripts/build_compiler.ps1` to build standalone `bin/kale.exe` via PyInstaller

## Coding Conventions
- Python code follows standard Python conventions
- Tests in `tests/` directory using pytest

## Short-term Milestones
- [ ] Add f32/f64 float types
- [ ] Add -l linker flag for external libraries
- [ ] Struct-by-value returns
- [ ] Method chaining
- [ ] Trait/interface system

## Future Plans
Self-hosting — rewrite compiler in Kale itself.
