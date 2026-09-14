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
