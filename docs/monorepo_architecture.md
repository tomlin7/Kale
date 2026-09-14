# Kale Monorepo Architecture & Standards

This document establishes the repository structure, conventions, and guidelines for the Kale Monorepo. The monorepo is engineered to host the core compiler, standard library, developer tooling, ecosystem libraries, operating system kernel/userland, and flagship applications in a unified codebase.

---

## 1. Directory Taxonomy

```
kale/
├── packages/                      # Core Compiler, Runtime & Toolchain
│   ├── std/                       # Official Standard Library (.kl)
│   │   ├── core/                  # Primitives, memory, math, basic pointers
│   │   ├── io/                    # Console, file I/O, buffered streams
│   │   ├── sys/                   # OS calls, environment, process management
│   │   └── collections/           # Dynamic arrays, maps, strings, buffers
│   └── compiler/                  # Reference compiler & intermediate representations
│
├── libs/                          # Shared Ecosystem Libraries & Frameworks
│   ├── ui/                        # Cross-platform GUI framework (widgets, render engine)
│   ├── web/                       # High-performance web framework (routing, middleware)
│   ├── sql/                       # Database driver & query builder
│   └── net/                       # TCP/UDP networking, HTTP client/server, TLS
│
├── apps/                          # Flagship Applications
│   ├── editor/                    # Native Kale code editor
│   ├── vcs/                       # Distributed Version Control System & forge (Git alternative)
│   ├── blog/                      # Kale-powered blogging & publishing platform
│   └── android-bootstrapper/      # Android app scaffolding & build packager
│
├── sys/                           # Bare-Metal & Operating System
│   ├── boot/                      # Bootloader stages (x86_64 / ARM64)
│   ├── kernel/                    # Microkernel/monolithic kernel written in Kale & assembly
│   └── drivers/                   # Device drivers (storage, display, timers, UART)
│
├── tools/                         # Developer Tooling & Automation
│   ├── scripts/                   # Monorepo build, test, and release runners
│   └── vscode/                    # Syntax highlighting & Language Server Protocol (LSP)
│
├── docs/                          # Architecture Specifications & RFCs
├── examples/                      # Language showcases and sample programs
├── tests/                         # Unit, integration, and end-to-end compiler test suites
└── src/                           # Compiler implementation (Python bootstrap / self-hosting)
```

---

## 2. Monorepo Package Standards

1. **Self-Contained Modules**: Every library under \libs/\ and app under \pps/\ must maintain its own documentation and design specs.
2. **Import Conventions**:
   - Relative imports (\./helper.kl\, \../common.kl\) are used within the same package.
   - Standard library imports (\std/core/math.kl\, \std/io/print.kl\) are resolved via the compiler search paths.
   - Shared library imports (\libs/ui/window.kl\, \libs/sql/db.kl\) are resolved via the monorepo root.
3. **No Circular Dependencies Across Packages**:
   - \pps/*\ may depend on \libs/*\ and \packages/std\.
   - \libs/*\ may depend on \packages/std\.
   - \packages/std\ has no external dependencies.
   - \sys/*\ interacts with bare metal and hardware abstractions directly.
