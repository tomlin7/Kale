<table>
  <td>
    <img src="./logo.svg" height=80 />
  </td>
</table>

# Kale &nbsp;·&nbsp; Autonomous Monorepo Ecosystem

> Architectural Precision. Deterministic Systems.
>
> A statically-typed compiled language with direct **LLVM 18 IR** emission, stack-allocated data structures, zero GC, and sub-millisecond graphics — built entirely in Kale.

```
pip install kale-lang        # compiler & CLI
```

→ **[Website](https://tomlin7.github.io/Kale)** &nbsp;·&nbsp; **[PyPI](https://pypi.org/project/kale-lang/)** &nbsp;·&nbsp; **[Actions](https://github.com/tomlin7/Kale/actions)**

---

## Monorepo Map

### ⚙ Core Toolchain

| Project | Path | Description |
|---------|------|-------------|
| **Kale Compiler** | [`src/kale/`](src/kale/) | LLVM 18 IR emitter, Pratt parser, binder, JIT & AOT via Clang/LLD |
| **packages/std** | [`packages/std/`](packages/std/) | Standard library — collections, strings, I/O, memory, generics |
| **tools/pkg** | [`tools/pkg/`](tools/pkg/) | `kale-pm` package manager & manifest resolver |

### 🖥 Flagship Apps

| Project | Path | Description |
|---------|------|-------------|
| **Kale Editor** | [`editor/`](editor/) | 144 Hz GPU-accelerated code editor, piece table buffer, font atlas |
| **Kale VCS** | [`vcs/`](vcs/) | Distributed VCS — pure-Kale SHA-1, DAG object store, porcelain CLI |
| **apps/lsp** | [`apps/lsp/`](apps/lsp/) | Language Server Protocol server for IDE integration |
| **apps/kv** | [`apps/kv/`](apps/kv/) | High-performance key-value daemon |

### 📦 Foundation Libraries

| Project | Path | Description |
|---------|------|-------------|
| **libs/render** | [`libs/render/`](libs/render/) | 2D GPU batch renderer, SDF rects, dynamic font atlas (stb_truetype) |
| **libs/ui** | [`libs/ui/`](libs/ui/) | Immediate-mode widget toolkit — buttons, sliders, scrollers, layout stacks |
| **libs/framework** | [`libs/framework/`](libs/framework/) | App harness — GLFW3 window, OpenGL context, frame pacing, input dispatch |
| **libs/net** | [`libs/net/`](libs/net/) | Raw sockets & HTTP/1.1 engine |
| **libs/web** | [`libs/web/`](libs/web/) | Lightweight HTTP router & JSON responder |
| **libs/sql** | [`libs/sql/`](libs/sql/) | SQLite3 FFI bindings & query builder |
| **libs/tls** | [`libs/tls/`](libs/tls/) | TLS 1.3 client over raw sockets |
| **libs/audio** | [`libs/audio/`](libs/audio/) | PCM audio playback & mixer |
| **libs/physics** | [`libs/physics/`](libs/physics/) | 2D rigid body physics engine |
| **libs/term** | [`libs/term/`](libs/term/) | ANSI terminal engine & TUI widgets |
| **libs/fs_watch** | [`libs/fs_watch/`](libs/fs_watch/) | Cross-platform filesystem watcher |

### 🔩 Low-Level & OS

| Project | Path | Description |
|---------|------|-------------|
| **sys/ (Kale OS)** | [`sys/`](sys/) | Bare-metal x86_64 kernel — Multiboot, IDT, paging, direct framebuffer |
| **sys/sysmon** | [`sys/`](sys/) | Real-time system monitor & diagnostics dashboard |

### 🔌 Tooling & Packages

| Project | Path | Description |
|---------|------|-------------|
| **packages/bindings** | [`packages/bindings/`](packages/bindings/) | Win32, GLFW3, OpenGL FFI binding headers |
| **packages/vscode-kale** | [`packages/vscode-kale/`](packages/vscode-kale/) | VS Code extension — syntax highlighting & snippets |
| **website** | [`website/`](website/) | Next.js project showcase site |

---

## Quick Start

```bash
# Install
pip install kale-lang

# Run a program (LLVM JIT)
kale run examples/fibonacci.kl

# Compile to native binary
kale build examples/fibonacci.kl -o fib.exe

# Typecheck only
kale check examples/fibonacci.kl

# Dump LLVM IR
kale dump-llvm examples/fibonacci.kl
```

## Compiler Pipeline

```
Source .kl  →  Lexer  →  Pratt Parser  →  AST Binder  →  LLVM 18 IR  →  LLD  →  x86_64
```

## Development

```bash
uv sync          # install deps
uv run pytest    # run test suite (~60 tests)
uv build         # build wheel + sdist
```

---

<sub>MIT License · Built with Python & llvmlite · Requires Python ≥ 3.10</sub>
