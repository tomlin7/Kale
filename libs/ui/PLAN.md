# GPU Immediate-Mode UI Toolkit (`libs/ui`) Plan

## 1. Overview
`libs/ui` provides a state-of-the-art immediate-mode user interface library for Kale desktop software. It bypasses retained DOM/widget trees in favor of frame-by-frame procedural composition, delivering sub-millisecond responsiveness and zero state-synchronization overhead.

---

## 2. Directory Layout & Module Specifications

```
libs/ui/
├── ui.kl            # UIContext, hot/active widget tracking, ID generation
├── widgets.kl       # Button, Label, TextInput, Checkbox, Slider, Scrollbar
├── layout.kl        # Row, Column, Padding, Auto-sizing boxes
├── theme.kl         # Color schemes (Dark, Light, Custom)
├── clipboard.kl     # System clipboard integration
└── PLAN.md
```

---

## 3. Immediate-Mode Architecture

### 3.1 Frame Lifecycle
```
ui_begin(ctx);

if (ui_button(ctx, "Save File", 20.0f, 20.0f, 120.0f, 32.0f)) {
    save_current_document();
}

ui_label(ctx, "Status: Ready", 20.0f, 60.0f);

ui_end(ctx); // Flushes all generated geometry to libs/render
```

### 3.2 Widget ID & State Tracking
- Every interactive element has an integer/string ID (derived from position or explicit salt).
- The `UIContext` tracks:
  - `hot_id`: Widget hovered by mouse cursor.
  - `active_id`: Widget currently clicked / receiving input.
  - `focused_id`: Widget receiving keyboard strokes.

### 3.3 Core Widgets
- **`ui_button(ctx, text, x, y, w, h) -> bool`**: Renders rounded button, changes color on hover/press, returns true on mouse release.
- **`ui_label(ctx, text, x, y)`**: Renders styled text span.
- **`ui_text_input(ctx, id, buffer, x, y, w, h) -> bool`**: Interactive text box with cursor caret, backspace, selection, and clipboard support.
- **`ui_scrollbar(ctx, id, offset, content_height, view_height, bounds) -> float32`**: Interactive scrolling thumb.
