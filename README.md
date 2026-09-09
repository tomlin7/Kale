<table>
  <td>
    <img src="./logo.svg" height=100 />
  </td>
</table>

# Kale
> A modern, statically-typed compiled programming language and LLVM-backed compiler pipeline written in Python, powered by `uv`.

Kale compiles source code (`.kl`) directly into **LLVM Intermediate Representation (IR)** with in-memory **JIT execution** and native standalone binary compilation via **Clang / LLD**.

---

## Architecture Overview

Kale is built upon a clean, decoupled multi-stage compiler pipeline:

```
Source Code (.kl)
       │
       ▼
   [ Lexer ]  ──────────────► [ DiagnosticBag ]
       │                      (Errors & Warnings with line:column carets)
       ▼
 [ Syntax Tokens ]
       │
       ▼
 [ Pratt Parser ]
       │
       ▼
 [ Abstract Syntax Tree (AST) ]
       │
       ▼
 [ Semantic Analyzer / Binder ] ──► [ Lexical Scopes & Type Checking ]
       │
       ▼
 [ Bound AST / Program ]
       │
       ▼
 [ LLVM IR Emitter ] ──────────► [ In-Memory LLVM JIT Engine ] (Instant execution)
       │
       ▼
 [ Clang / LLD Native Driver ] ─► Native Executable (.exe / binary)
```

### Compiler Subsystems

- **`kale.diagnostics`**: Source position tracking (`TextSpan`, `TextLocation`), line mapping, and compiler diagnostics with color-coded snippets and carets.
- **`kale.syntax`**: Non-colliding `SyntaxKind` tokens, robust scanner supporting multi-character operators, numbers (integer, float, exponent), strings with full escape handling, and block/line comments.
- **`kale.ast`**: Strongly-typed AST nodes for expressions, declarations, loops, conditionals, and statements. Includes an `AstPrinter` for tree visualization.
- **`kale.parser`**: Recursive descent for statements combined with Pratt parsing (operator precedence climbing) for expressions, complete with error synchronization/recovery.
- **`kale.binding`**: Semantic analysis pass implementing hierarchical lexical scopes, variable shadowing, constant immutability, numeric promotion, and type validation.
- **`kale.codegen`**: 
  - **LLVM Emitter & JIT**: Generates typed LLVM IR and executes in-memory via LLVM ORC/MCJIT.
  - **LLVM Driver**: Invokes Clang to compile `.ll` into native standalone executables.
  - **C Emitter**: Optional fallback backend targeting standard C99.

---

## Quick Start with `uv`

### Installation & Environment Setup

Kale uses [`uv`](https://github.com/astral-sh/uv) for lightning-fast environment and dependency management:

```bash
# Sync dependencies and create virtual environment instantly
uv sync
```

### Running Programs

```bash
# Execute instantly in-memory via the LLVM JIT engine
uv run kale run examples/fibonacci.kl

# Build a native standalone executable (.exe) via Clang
uv run kale build examples/fibonacci.kl -o fib.exe
./fib.exe

# Dump generated LLVM Intermediate Representation (IR)
uv run kale dump-llvm examples/fibonacci.kl

# Typecheck and validate without compiling
uv run kale check examples/fibonacci.kl

# Inspect parsed AST tree
uv run kale dump-ast examples/fibonacci.kl

# Inspect scanned token stream
uv run kale dump-tokens examples/hello.kl
```

---

## Language Features

### Variables & Types

```kale
int a = 10;
double pi = 3.14159;
bool flag = true;
string greeting = "Hello, Kale!";
let deduced = 42;          // Type deduced as int
const max_users = 100;     // Read-only constant
```

### Control Flow

```kale
// If - Else
if (a > 5) {
    print("Greater than 5");
} else {
    print("5 or less");
}

// While Loops
int i = 0;
while (i < 5) {
    print(i);
    i++;
}

// For Loops
for (int j = 0; j < 5; j++) {
    print(j);
}
```

---

## Running Tests

Run the full test suite (30 unit & integration tests across diagnostics, lexer, parser, binder, LLVM emitter, JIT, and Clang driver) using `uv`:

```bash
uv run pytest
```
