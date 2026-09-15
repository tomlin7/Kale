# Kale Master Ecosystem Architecture Plan

## Executive Summary
This document defines the canonical engineering master plan for the entire Kale ecosystem. It governs all 17 sub-projects across the monorepo, detailing the foundational layers, architecture decisions, inter-project contracts, and the progressive build sequence leading to a fully self-hosting language and flagship software suite.

---

## 1. Monorepo Taxonomy & Project Registry

The repository is structured into four functional tiers: Core/Toolchain, Foundation Libraries, Frameworks & UI, and Flagship Applications.

```
kale/
├── src/kale/                     # Tier 0: PythonKale Compiler (v0.2.0)
├── packages/                     # Tier 1: Core Standard Library & Low-level Bindings
│   ├── std/                      # Kale Standard Library (v0.2.0)
│   ├── bindings/win32/           # Win32 OS & GDI FFI Bindings (v0.1.0)
│   └── editor/                   # Legacy Editor Core (v0.1.0, deprecated)
├── libs/                         # Tier 2: Foundation & Framework Libraries
│   ├── glfw/                     # GLFW3 Windowing & Input FFI (v0.0.1)
│   ├── gl/                       # OpenGL 3.3 Core Profile & Loader (v0.0.1)
│   ├── stb/                      # stb_truetype & stb_image FFI (v0.0.1)
│   ├── render/                   # 2D Batched GPU Graphics & Font Engine (v0.0.1)
│   ├── ui/                       # GPU Immediate-Mode Widget Toolkit (v0.0.1)
│   ├── ui_native/                # Native Win32 GDI Widget Toolkit (v0.1.0)
│   ├── framework/                # App Bootstrap & Lifecycle Harness (v0.1.0 -> v0.2.0)
│   ├── net/                      # Sockets & HTTP/1.1 Networking (v0.0.1)
│   ├── web/                      # Server Router & Template Engine (v0.0.1)
│   └── sql/                      # SQLite3 Database Driver & Query Builder (v0.0.1)
├── editor/                       # Tier 3: Kale Flagship Code Editor / IDE (v0.1.0 -> v0.2.0)
│   └── supercharges/             # Split panes, LSP client, fuzzy file finder
├── vcs/                          # Tier 3: Distributed Version Control System (v0.0.1)
├── apps/
│   ├── blog/                     # ⏸️ POSTPONED (Awaiting explicit user trigger)
│   ├── kv/                       # In-memory Redis-compatible key-value store (kaledis)
│   └── lsp/                      # Language Server Protocol (LSP) Server
├── tools/
│   └── pkg/                      # Package manager & build tool (kale-pm)
├── os/                           # Tier 4: Low-Level OS & Bare-Metal Kernel
│   ├── boot/                     # Multiboot / UEFI Bootloader
│   ├── kernel/                   # Microkernel in Kale + ASM
│   ├── drivers/                  # Hardware Abstraction Drivers
│   ├── sysmon/                   # Terminal & Process Monitor
│   └── dig/                      # DNS packet resolver & CLI
├── libs/                         # Foundation Libraries (Expanded)
│   ├── term/                     # Virtual terminal emulator & VT100 parser
│   ├── fs_watch/                 # Cross-platform filesystem watcher
│   ├── audio/                    # Low-latency PCM sound & audio mixing engine
│   ├── vg/                       # Vector graphics & 2D canvas API
│   ├── physics/                  # 2D rigid body physics engine
│   └── tls/                      # Cryptography suite & TLS 1.3
├── website/                      # Renaissance-themed Next.js Monorepo Portal
├── plans/                        # Master Planning & Milestone Directives
└── tests/                        # Comprehensive E2E & Unit Test Suites
```

---

## 2. Core Architectural Principles & Decisions

### 2.1 Native GPU Rendering Pipeline (`libs/gl` + `libs/render` + `libs/ui`)
1. **API Selection**: OpenGL 3.3 Core Profile over Vulkan for v1.
   - *Rationale*: Zero runtime shader compilation jank, ubiquity across all Intel/AMD/Nvidia GPUs without driver fragmentation, and radically simpler FFI surface compared to Vulkan's 2000+ line initialization boilerplate.
2. **Windowing & Context**: GLFW3 (`libs/glfw`).
   - *Rationale*: Lean, battle-tested C library strictly handling window creation, input dispatch, and GL/Vulkan context initialization.
3. **Typography & Geometry**:
   - `stb_truetype` vendored in `libs/stb/vendor/` to rasterize glyphs into a dynamic texture atlas cache.
   - Batched 2D rendering in `libs/render/batch.kl`: Dynamic VBO/EBO holding vertex structs `[x, y, u, v, r, g, b, a]`.
   - Drawing rects, rounded borders, text spans, and clips in 1-3 draw calls per frame.
4. **Immediate-Mode UI**:
   - `libs/ui` uses immediate-mode patterns (`ui_button`, `ui_text_input`, `ui_label`).
   - State is stored externally or keyed by widget ID hash; eliminates complex UI tree synchronization and event bubbling bugs.

### 2.2 Application Framework (`libs/framework`)
- Centralizes application loop: initialization, frame delta calculation, event collection from GLFW, UI frame dispatch, buffer swapping, and clean shutdown.
- Apps implement a simple lifecycle: `app.init(...)`, `while app.poll_event(...)`, `app.present()`.

### 2.3 Web & Network Stack (`libs/net` + `libs/web` + `libs/sql`)
- Raw TCP/UDP via Winsock2 (`ws2_32`) on Windows and Berkeley sockets on POSIX.
- HTTP/1.1 client with connection reuse; single-threaded non-blocking HTTP server with epoll/select model.
- `libs/web` provides trie/regex based routing, request/response models, middleware pipeline, and mustache-style template rendering.
- `libs/sql` wraps SQLite3 C ABI (`sqlite3_prepare_v2`, `sqlite3_step`) for embedded SQL storage.

### 2.4 Standalone Applications
- **Editor (`editor/`)**: High-performance text editor powered by `packages/std/text/piece_table.kl`, GPU text viewport, syntax tokenizer, gutter with line numbers, and status bar.
- **VCS (`vcs/`)**: Git-compatible object store (content-addressable SHA-1 blobs, trees, commits, index, packfiles).

---

## 3. Inter-Project Dependency Graph

```
[src/kale (Compiler)]
        │
        ▼
[packages/std] ────────────────────────┐
        │                              │
        ├──► [packages/bindings/win32] │
        │            │                 │
        │            ▼                 │
        │     [libs/ui_native]         │
        │            │                 │
        │            ▼                 │
        │       [editor v1]            │
        │                              │
        ├──► [libs/glfw]               ├──► [libs/net]
        │         │                    │         │
        ├──► [libs/gl]                 │         ▼
        │         │                    │    [libs/web]
        ├──► [libs/stb]                │
        │         │                    │
        │         ▼                    │
        └──► [libs/render]             │
                  │                    └──► [libs/sql]
                  ▼                              │
             [libs/ui]                           ▼
                  │                            [vcs]
                  ▼
          [libs/framework v2]
                  │
                  ▼
             [editor v2]
```

---

## 4. Per-Project Governance & Versioning Standards

1. **Semantic Versioning**: All packages strictly adhere to `MAJOR.MINOR.PATCH`.
2. **Project Documentation**: Every single directory must contain:
   - `agents.md`: Operational guidelines, status, build commands, and short milestones for AI agents.
   - `PLAN.md`: Full architectural blueprint, module breakdown, data structures, and implementation roadmap.
3. **Language & Linking Conventions**:
   - All Kale modules (.kl) must be modular and independently testable.
   - C bindings use `extern fn` matching target ABI data representations.
   - Struct names are `PascalCase`, functions and variables are `snake_case`.
   - Raw pointers are encapsulated behind typed structs wherever possible.
