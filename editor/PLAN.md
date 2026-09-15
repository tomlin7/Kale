# Flagship Code Editor (`editor`) Plan

## 1. Overview
`editor` is the flagship IDE demonstration for the Kale programming language. Written natively in Kale, it leverages `packages/std/text/piece_table.kl`, `libs/render` (GPU batching), and `libs/ui` to achieve sub-millisecond keystroke-to-render latency.

---

## 2. Directory Layout & Subsystems

```
editor/
├── main.kl          # Application entry point, event loop, layout split
├── app_state.kl     # EditorState: piece table, cursors, dirty flag, file paths
├── text_viewport.kl # Text rendering canvas, viewport culling, caret animation
├── gutter.kl        # Line numbers, breakpoint margins, folding indicators
├── status_bar.kl    # Mode indicator, line/column tracking, UTF-8, file size
├── command_bar.kl   # Command palette & fuzzy file opener (Ctrl+P / Ctrl+Shift+P)
└── PLAN.md
```

---

## 3. Evolutionary Architecture Phases

### Phase 1: Prototype (Completed)
- Uses `libs/framework` v1 (Win32 GDI) and `libs/ui_native`.
- Proved PieceTable text buffer integration, live token highlighting, and basic cursor navigation.

### Phase 2: GPU Migration (Completed)
- Migrated to `libs/framework` v2 (GLFW3 + OpenGL 3.3 Core Profile).
- Text rendering executed via `libs/render/batch.kl` and `libs/render/font.kl`:
  - Each character is rendered as a quad sampled from the glyph atlas.
  - Syntax coloring applied via per-vertex color components.
  - Zero allocation during scrolling or typing.
- Active line highlight, interactive gutter line numbers, and status bar.

### Phase 3: IDE Capabilities (In Progress)
- Multi-line selection and mouse drag selection.
- File tree sidebar exploring workspace directories (`packages/std/fs/dir.kl`).
- Multiple open tabs with Ctrl+Tab switching and persistent per-tab buffers.
- Horizontal/vertical split buffers.
- Search and replace with regular expressions.
- Command palette fuzzy finder.
