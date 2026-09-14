# Kale Long-Term Strategic Roadmap

This document outlines the overarching architectural direction and long-term milestones for the **Kale Programming Language**.
The mission is to establish Kale as a premier, high-performance systems language with a self-sufficient ecosystem spanning native GUI applications, web engines, low-level OS components, and self-hosted compilers.

---

## 🏛️ Strategic Pillars

```
+-------------------------------------------------------------------------------+
|                           Kale Ecosystem Vision                               |
+-------------------------------------------------------------------------------+
|  Tier 3: Flagship Applications                                                |
|  - apps/editor: GPU-accelerated, sub-millisecond latency code editor / IDE     |
|  - apps/vcs: Distributed version control system (Git alternative)             |
|  - apps/blog: High-throughput CMS & web publishing platform                   |
|  - apps/android-bootstrapper: Native Android APK compiler & scaffolding       |
+-------------------------------------------------------------------------------+
|  Tier 2: Foundation & Framework Libraries                                     |
|  - libs/ui: Immediate-mode GPU widget toolkit (custom rendering)              |
|  - libs/render: 2D batched graphics, texture atlasing, font SDF               |
|  - libs/gl & libs/glfw & libs/stb: Core graphics, windowing, and media FFI    |
|  - libs/framework: Cross-platform application bootstrap harness               |
|  - libs/web & libs/net & libs/sql: High-performance backend & database stack  |
+-------------------------------------------------------------------------------+
|  Tier 1: Core Toolchain & Runtime Base                                        |
|  - packages/std: Comprehensive standard library (core, collections, fs, text) |
|  - packages/compiler: Self-hosted Kale compiler (Kale written in Kale)        |
|  - LLVM IR generation, native AOT compilation, and JIT execution              |
+-------------------------------------------------------------------------------+
|  Tier 0: Operating System & Hardware Abstraction (sys/*)                     |
|  - sys/boot: Multiboot / UEFI x86_64 bootloader                               |
|  - sys/kernel: Microkernel in Kale + ASM                                      |
|  - sys/drivers: Device drivers (VGA, Framebuffer, VirtIO, Serial)             |
+-------------------------------------------------------------------------------+
```

---

## 🎯 Pillar 1: High-Performance GPU GUI & Flagship IDE
To prove Kale's power in interactive systems programming:
1. **Custom GPU Rendering**: Complete elimination of slow GDI/Win32 drawing routines in favor of high-throughput OpenGL 3.3 / Vulkan batched quads.
2. **Flagship Editor (`apps/editor`)**:
   - Sub-millisecond input-to-render loop.
   - Arbitrary file handling using Piece Table buffer data structure.
   - Real-time lexical and syntax token coloring.
   - Multiple split panes, command palette, and extensible plugin architecture.

---

## 🌐 Pillar 2: Systems Networking & Web Ecosystem
A fully native backend stack for web servers and distributed systems:
1. **Low-Overhead Networking (`libs/net`)**:
   - Non-blocking socket I/O using epoll/IOCP/kqueue abstractions.
   - HTTP/1.1 and HTTP/2 transport engines.
2. **Modern Web Framework (`libs/web`)**:
   - High-throughput trie-based router matching hundreds of thousands of requests per second.
   - Server-side templating and JSON serialization.
3. **Embedded Storage (`libs/sql`)**:
   - Zero-dependency relational database interaction via SQLite3.

---

## 📦 Pillar 3: Self-Hosting & Language Autonomy
Transitioning from PythonKale to a fully self-hosting compiler:
1. **Phase 1 (PythonKale Stabilization)**: Feature-complete type checker, generics, struct-by-value pass/return, floats, and robust diagnostics.
2. **Phase 2 (Kale in Kale)**: Re-implementing the lexer, parser, type checker, and LLVM emitter in Kale itself.
3. **Phase 3 (Triangular Bootstrap)**: PythonKale compiles Kale compiler source -> `kale1.exe`. `kale1.exe` compiles itself -> `kale2.exe`. Verifying `sha256(kale1.exe) == sha256(kale2.exe)`.

---

## 💻 Pillar 4: Bare-Metal Systems & Kale OS (`sys/*`)
Taking Kale directly to bare-metal x86_64 hardware:
1. **Bootloader (`sys/boot`)**: Stage 1 MBR & Stage 2 protected mode loader transition to 64-bit long mode.
2. **Kernel (`sys/kernel`)**:
   - Memory management: Physical page frame allocator, virtual paging table setup.
   - Interrupt handling: IDT, PIC/APIC controllers, timer interrupts.
   - Process scheduler: Preemptive multitasking, context switching in ASM.
3. **Framebuffer Display (`sys/drivers`)**: Linear framebuffer driver rendering Kale UI directly onto bare hardware without an underlying OS.
4. **Terminal & Process Monitor (`sys/sysmon`)**: Bare-metal & native real-time CPU, memory, thread, and process inspection TUI tool.
5. **DNS Resolver & Diagnostic CLI (`sys/dig`)**: Low-level packet-crafted DNS query tool and resolver for systems networking.

---

## ⚡ Pillar 5: Low-Level Foundation & Terminal Emulation
1. **Terminal Core (`libs/term`)**: Virtual terminal emulator, ANSI/VT100 escape sequence parser, and pty abstraction for terminal-based apps.
2. **Filesystem Watcher (`libs/fs_watch`)**: Real-time cross-platform filesystem event notification engine (`ReadDirectoryChangesW`, `inotify`, `kqueue`).
3. **Low-Latency Audio Engine (`libs/audio`)**: Native audio mixing, PCM stream processing, and multi-channel sound synthesis via WASAPI/CoreAudio/ALSA.
4. **Vector Graphics & Canvas 2D (`libs/vg`)**: Anti-aliased cubic Bézier curves, path rasterization, stroke caps, and vector rendering.
5. **2D Physics Engine (`libs/physics` / `games/arcade`)**: Rigid-body collision detection, spatial hashing, GJK/EPA, impulse resolution, and interactive game physics.
6. **TLS & Cryptography Suite (`libs/tls`)**: Native implementation of ChaCha20-Poly1305, AES-GCM, SHA-256/512, and TLS 1.3 handshake state machine.
7. **High-Performance In-Memory Key-Value Store (`apps/kv` / `kaledis`)**: RESP-compatible in-memory database with append-only persistence and concurrent lock-free skip lists.

---

## 🛠️ Pillar 6: Developer Tooling & Ecosystem Infrastructure
1. **Language Server Protocol Server (`apps/lsp` / `tools/lsp`)**: High-performance LSP server delivering jump-to-definition, hover docs, completions, and real-time semantic diagnostics.
2. **Editor Supercharges (`editor/`)**: Deep LSP client integration, fuzzy project finder, tree-sitter or native Kale AST folding, Git gutter indicators, and split panes.
3. **Package Manager & Build Automation (`kale-pm` / `tools/pkg`)**: Monorepo dependency resolution, package registry client, lockfiles, and hermetic reproducible build pipeline.
4. **Web & Community**:
   - High-throughput CMS & web publishing platform (`apps/blog` - *⏸️ Postponed until explicit command*).
   - Kale Official Showcase Website (`website/`): Next.js Renaissance-themed portal highlighting all monorepo projects, architecture blueprints, interactive API specs, and benchmarks.

