# Milestone 31: Composited Window Manager & Alpha Blending Engine

## Overview
Implement the Composited Window Manager and 32-bit ARGB Alpha Blending Engine for Kale OS. Upgrades the desktop graphics environment from single-buffer drawing to offscreen surface compositing, Z-order layer sorting, Porter-Duff Over alpha blending, dirty region invalidation, and interactive window decorations.

## Technical Architecture
1. **Porter-Duff Alpha Blending**:
   - Computes standard linear alpha blending:
     $$C_{out} = \frac{C_s \cdot \alpha_s + C_d \cdot (255 - \alpha_s)}{255}$$
   - Handles ARGB color packing `(A << 24) | (R << 16) | (G << 8) | B`.
2. **Window Surface Model (`WindowSurface`)**:
   - Dimensions: position `(x, y)`, size `(w, h)`, and clipping bounds.
   - State flags: `WIN_FLAG_VISIBLE`, `WIN_FLAG_FOCUSED`, `WIN_FLAG_TRANSLUCENT`, `WIN_FLAG_MINIMIZED`.
   - Z-ordering: Layer integer determines back-to-front rendering order.
   - Title bar metrics: Height (typically 20-24px), close button bounds, active title color.
3. **Compositor Pipeline (`Compositor`)**:
   - Screen bounds (e.g. 1024x768 or 800x600).
   - Window registry: Tracks up to 16 concurrent top-level window surfaces.
   - Focus management: Brings focused window to top of Z-order stack.
   - Clipping & damage rectangles: Clips window pixels strictly to screen coordinates `[0..width, 0..height]`.
   - Cursor overlay: Composites hardware/software mouse cursor above all window layers.

## Deliverables
- `os/plans/031_window_compositor.md`: Architecture specification.
- `os/kernel/compositor.kl`: Pure Kale window compositor, alpha blending math, Z-order sorter, and window surface manager.
- `tests/test_os_window_compositor.py`: Test suite validating alpha blending calculations, Z-ordering, window creation, focus switching, coordinate clipping, and drag movement.
