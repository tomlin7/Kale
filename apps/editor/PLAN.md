# apps/editor Architecture Plan

## 1. Overview
The Supercharged Kale Flagship Code Editor & Integrated Development Environment (IDE). Features multi-buffer management, piece-table text buffers, and a native embedded terminal emulator split powered by `libs/term`.

## 2. Modules
- `buffer_manager.kl`: Multi-file document buffer manager with 8 buffer slots, slot compaction, active buffer switching, tab registry, dirty state tracking, and piece-table buffer lifecycle.
- `terminal_split.kl`: Terminal emulator split integration powered by `libs/term`. Handles split layout orientation (horizontal bottom / vertical right), dynamic resizing (`split_resize`, `split_set_percent`), pane toggling, keyboard focus switching, ANSI VT sequence streaming, and cell grid rendering.
- `layout.kl`: Viewport split geometry calculator partitioning the window between editor panes, terminal panes, tabs bar, and status bar.
- `main.kl`: IDE application harness orchestrating buffer management, terminal execution, and verification.

## 3. Terminal Split Capabilities
- Embedded VT100 / ANSI TrueColor virtual terminal grid (`80x24` or responsive sizing via `split_resize`).
- Zero-latency IPC / streaming from sub-processes (compiler output, test results, shell commands).
- Hotkey toggle for terminal split pane (e.g. `Ctrl+\``) and buffer switching (e.g. `Ctrl+Tab` or tab clicks).
