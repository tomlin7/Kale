# UI Native (`libs/ui_native`) Architecture Plan

## 1. Overview
`libs/ui_native` provides a lightweight, pure GDI-based widget library for Windows desktop applications requiring zero external GPU dependencies.

---

## 2. Module Layout
- `geom.kl`: Geometric structures (`Point`, `Rect`, `Color`, `Padding`) with bounds checking and `COLORREF` conversions.
- `event.kl`: Native event definitions (Key, Mouse, Click, Resize, Close).
- `canvas.kl`: Double-buffered offscreen rendering using GDI `CreateCompatibleDC` and `BitBlt`.
- `widgets/`:
  - `label.kl`: Read-only text display with configurable font and background.
  - `button.kl`: Interactive push button with hover, pressed, and click states.
  - `container.kl`: Panel box container for layout organization.

---

## 3. Short-Term Enhancements
1. **Single-line Text Input (`widgets/text_input.kl`)**: Implement basic interactive text input field with cursor caret.
2. **Scrollbar Widget (`widgets/scrollbar.kl`)**: Add scrollbar handle and track for panning larger canvas areas.
3. **Stabilization**: Keep pure Win32 API compatibility intact for lightweight fallback utilities.
