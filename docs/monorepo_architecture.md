# Kale Monorepo Architecture & Engineering Guidelines

## 1. Overview & Directory Taxonomy

The Kale monorepo houses the compiler, standard library, platform bindings, foundation libraries, application frameworks, and flagship end-user applications.

```
kale/
├── packages/                      # Core Compiler, Runtime & Toolchain
│   ├── std/                       # Official Standard Library (.kl)
│   │   ├── core/                  # Math, string, option, result
│   │   ├── collections/           # Generic list, buffer, map
│   │   ├── fs/                    # Path, dir, file_util
│   │   ├── io/                    # File stream I/O
│   │   ├── sys/                   # Process, system wrappers
│   │   └── text/                  # Piece table, string builder
│   ├── bindings/                  # Low-Level Foreign Function Interfaces
│   │   └── win32/                 # Windows user32, gdi32, kernel32
│   └── editor/                    # Legacy editor engine (deprecated)
│
├── libs/                          # Foundation & Framework Libraries
│   ├── glfw/                      # GLFW3 windowing & input bindings
│   ├── gl/                        # OpenGL 3.3 Core Profile bindings & loader
│   ├── stb/                       # stb_truetype & stb_image FFI
│   ├── render/                    # 2D batched GPU graphics & font engine
│   ├── ui/                        # GPU-accelerated immediate-mode widget toolkit
│   ├── ui_native/                 # Win32 GDI widget toolkit (legacy desktop)
│   ├── framework/                 # Cross-platform application bootstrap harness
│   ├── net/                       # Sockets & HTTP/1.1 networking
│   ├── web/                       # Web framework (routing, templates)
│   └── sql/                       # SQLite3 database driver & query builder
│
├── apps/                          # Flagship End-User Applications
│   ├── editor/                    # Native Kale code editor / IDE
│   ├── vcs/                       # Distributed version control system
│   ├── blog/                      # Web publishing platform & CMS
│   └── android-bootstrapper/      # Android cross-compilation toolchain
│
├── sys/                           # Bare-Metal Operating System (Future)
│   ├── boot/                      # x86_64 bootloader
│   ├── kernel/                    # Microkernel in Kale + ASM
│   └── drivers/                   # Hardware drivers
│
├── plans/                         # Master Roadmap & Short-Term Execution Plans
├── docs/                          # Architecture specs & documentation
├── examples/                      # Showcase programs & tutorials
├── tests/                         # Unit & integration test suites
└── src/kale/                      # Reference compiler implementation (Python bootstrap)
```

---

## 2. Monorepo Standards & Hygiene Rules

1. **Per-Project Documentation & Versioning**:
   - Every subfolder in `packages/`, `libs/`, and `apps/` MUST maintain:
     - `agents.md`: AI agent operational guide, SemVer tracking, build instructions, and local milestones.
     - `PLAN.md`: Deep technical design spec, data structures, module breakdown, and verification steps.
2. **Dependency Inversion & Boundary Rules**:
   - `apps/*` may depend on `libs/*`, `packages/std`, and `packages/bindings/*`.
   - `libs/*` may depend on other `libs/*` only according to the acyclic dependency graph defined in `plans/MASTER_ECOSYSTEM_PLAN.md`.
   - `packages/std` MUST NOT depend on any `libs/*` or `apps/*`. It interacts solely with the C runtime or core syscalls.
   - Circular imports between packages or libraries are strictly forbidden.
3. **Import Syntax**:
   - Internal imports within the same library: `import "libs/render/math.kl" as math;`
   - Standard library imports: `import "packages/std/collections/generic_list.kl" as gl;`
