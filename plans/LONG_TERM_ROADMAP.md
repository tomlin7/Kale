# Kale Long-Term Strategic Roadmap

This document outlines the overarching architectural direction and long-term milestones for the **Kale Programming Language**.
The goal is to evolve Kale from a low-level systems compiler into a self-hosting language capable of powering:
1. **A High-Performance Code Editor / IDE Engine** (comparable to Zed, Sublime Text, or Lite-XL).
2. **A Native Cross-Platform UI Framework** (GPU-accelerated, immediate & retained mode).
3. **Robust Systems Tooling & Standard Runtime** (package manager, language server protocol, build orchestrator).

---

## 🏛️ Strategic Pillars

```
+-----------------------------------------------------------------------+
|                       Kale Ecosystem Vision                           |
+-----------------------------------------------------------------------+
|  Tier 3: Flagship Applications                                        |
|  - Kale Editor (Sub-millisecond latency, Tree-Sitter / LSP, Text UI)  |
|  - Native Cross-Platform GUI Toolkit & Design System                  |
+-----------------------------------------------------------------------+
|  Tier 2: Core Infrastructure Libraries                                |
|  - std/text: Rope data structure, Piece Table, UTF-8 streaming        |
|  - std/fs: High-performance filesystem & async I/O traversal          |
|  - std/sync: Threading, atomics, work-stealing thread pools           |
|  - bindings/gpu & bindings/windowing (SDL2 / GLFW / WebGPU / Vulkan)  |
+-----------------------------------------------------------------------+
|  Tier 1: Compiler & Runtime Foundation (Current Base)                 |
|  - LLVM JIT & Native Object Compiler, C Emission Backend              |
|  - Generics & Monomorphization (List<T>, Option<T>, Result<T, E>)     |
|  - C FFI, Pointers, Structs, Heap/Arena Allocators                    |
+-----------------------------------------------------------------------+
```

---

## 🎯 Pillar 1: High-Performance Code Editor / IDE Engine

To prove Kale as a serious systems language, the primary flagship showcase application is a native, ultra-responsive code editor.

### Key Milestones:
- **Milestone 1.1: Text Buffers (`std/text`)**
  - High-performance Rope or Piece Table data structure supporting $O(\log N)$ inserts, deletes, line lookups, and piece caching.
  - UTF-8 byte offset <-> character/grapheme cluster indexing.
- **Milestone 1.2: Syntax Engine & Tokenization (`packages/syntax`)**
  - Streaming lexical tokenizer and Tree-Sitter C FFI integration for syntax highlighting and AST queries.
- **Milestone 1.3: Buffer View & Projection**
  - Line folding, word wrapping, multi-cursor selections, and virtual coordinate mappings.
- **Milestone 1.4: Language Server Protocol Client (`packages/lsp`)**
  - JSON-RPC over stdio, diagnostics rendering, completion popups, and symbol lookup.

---

## 🎨 Pillar 2: Native Cross-Platform UI Toolkit

A GPU-accelerated UI framework written natively in Kale to power the editor and future desktop applications.

### Key Milestones:
- **Milestone 2.1: Low-Level Windowing & Event Handling**
  - FFI integration with SDL2 / GLFW / Win32 API.
  - Native window creation, hardware input dispatch (mouse, keyboard, scroll, window resizing).
- **Milestone 2.2: 2D Canvas & Vector Graphics**
  - Integration with NanoVG / Skia / Sokol / Raylib / Direct2D.
  - Font rendering via FreeType / stb_truetype with glyph caching and subpixel positioning.
- **Milestone 2.3: Layout & Component Engine**
  - Flexbox-inspired or constraint-based layout engine (`packages/ui/layout`).
  - Retained & immediate-mode UI abstractions with dirty-rect clipping and reactive state updates.

---

## ⚙️ Pillar 3: Language Runtime, Standard Library & Concurrency

Expanding the core language runtime to support scalable, multithreaded systems.

### Key Milestones:
- **Milestone 3.1: Threading & Concurrency (`std/sync`)**
  - OS threads (`pthread` / Windows Threads), atomic primitives (`atomic_load`, `atomic_store`, `atomic_cas`).
  - Mutexes, condition variables, channels, and work-stealing job queue.
- **Milestone 3.2: Complete Systems I/O & Networking (`std/fs`, `std/net`)**
  - Directory iteration, recursive path walks, file metadata, memory-mapped files (`mmap`).
  - TCP / UDP sockets, non-blocking network streams.
- **Milestone 3.3: Self-Hosting Kale Compiler**
  - Re-writing the Python-based lexer, parser, binder, and LLVM emitter directly in Kale.
  - Bootstrapping Kale with self-compiled binaries.

---

## 📈 Long-Term Timeline Phases

| Phase | Focus Area | Primary Deliverables | Target Outcome |
|---|---|---|---|
| **Phase A** | Advanced Standard Library | `std/fs` path/dir walk, `std/text` piece table / rope, hash maps | Rich foundational stdlib for text/file manipulation |
| **Phase B** | Windowing & Graphics FFI | GLFW / SDL2 bindings, 2D renderer bindings | First native window opened & rendered via Kale |
| **Phase C** | Font & Text Layout Engine | Glyph atlas cache, line layout, text rendering | Crisp, real-time sub-millisecond code rendering |
| **Phase D** | Editor Core Architecture | Buffers, multi-cursor, undo/redo tree, command palette | Interactive, typing text editor prototype in Kale |
| **Phase E** | Concurrency & LSP | OS threads, async background workers, LSP client | Responsive IDE with syntax highlights and completions |
| **Phase F** | Self-Hosting Compiler | Kale compiler in Kale | True self-sufficiency and peak compile-time performance |
