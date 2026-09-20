# Milestone 9: Graphics Subsystem & Mouse Driver

## Overview
Implement a 32-bit linear framebuffer graphics subsystem, 2D rasterization engine, PS/2 mouse hardware driver, and multi-window canvas foundation for Kale OS. This milestone upgrades Kale OS from VGA 80x25 text mode into high-resolution graphical rendering (800x600, 1024x768) with double buffering, hardware scissor clipping, Bresenham line rendering, alpha channel compositing, bitmap font typography, packet-stream mouse tracking, and composited desktop window abstractions.

## Current State
- Milestone 1: Virtual Memory Manager (4-level paging, page fault handling)
- Milestone 2: Task Scheduler (PCB, 8254 PIT, preemptive context switching)
- Milestone 3: Interrupt Framework (IDT, PIC, keyboard, timer, ISR stubs)
- Milestone 4: System Call Interface (INT 0x80 / SYSCALL dispatcher, stats table)
- Milestone 5: User Space Support (ELF64 binary loader, TSS, Ring 3 privilege transitions)
- Milestone 6: Heap Allocator (Kernel heap, segregated size classes, coalescing free, user-space heap)
- Milestone 7: Virtual File System & Ramdisk (inode/vnode architecture, directory hierarchy, file descriptors)
- Milestone 8: Block Storage & ATA/IDE Disk Driver (ATA PIO mode, buffer cache, /dev/hda)
- Primitive framebuffer stub in `os/drivers/fb.kl` with unclipped pixel puts and flat fills
- No line drawing algorithm, no clipping rectangles, no alpha blending, no font rendering
- No mouse driver or packet decoding
- No window or desktop canvas abstractions

## Objectives
1. **Enhanced Framebuffer Graphics Driver (`os/drivers/fb.kl`)**:
   - Linear 32-bit ARGB/RGBA framebuffer structure (`Framebuffer`).
   - Resolution modes: 800x600x32, 1024x768x32, 640x480x32.
   - Double buffering: Front buffer and back buffer swap/blit (`fb_swap_buffers`).
   - Hardware scissor clipping viewport (`ClipRect`: `x1, y1, x2, y2`) ensuring safe rendering outside surface bounds.
   - High-performance 2D rasterization primitives:
     - `fb_put_pixel_clip`: Bounds-checked and scissor-clipped pixel plot.
     - `fb_draw_line`: Integer Bresenham's algorithm handling all 8 octants.
     - `fb_fill_rect_clip`: Fast span-based clipped rectangular filling.
     - `fb_draw_rect`: Outlined rectangular frame rendering.
     - `color_alpha_blend`: 32-bit ARGB alpha compositing `(fg * alpha + bg * (255 - alpha)) / 255`.
     - `fb_draw_char` and `fb_draw_string`: 8x8 bitmap font glyph rasterization with transparent or filled background.

2. **PS/2 Mouse Hardware Driver (`os/drivers/mouse.kl`)**:
   - Data port (`0x60`) and command/status port (`0x64`).
   - Initialization and streaming enable command sequence (`0xF4`).
   - 3-byte standard PS/2 packet decoding:
     - Byte 0: Button bits (Left, Right, Middle), sign bits (X sign, Y sign), overflow bits.
     - Byte 1: Delta X (sign-extended 9-bit relative motion).
     - Byte 2: Delta Y (sign-extended 9-bit relative motion, inverted Y coordinate).
   - Mouse state tracking (`MouseState`):
     - Screen position `x`, `y` clamped to display resolution bounds `[0, width - 1]` and `[0, height - 1]`.
     - Button states: `left_pressed`, `right_pressed`, `middle_pressed`.

3. **Window & Desktop Canvas Management (`os/kernel/window.kl`)**:
   - Window descriptor structure (`Window`):
     - Window ID, title, geometry rectangle (`x, y, width, height`).
     - Z-order priority, visibility, focus state.
     - Dirty rectangle tracker (`dirty_x, dirty_y, dirty_w, dirty_h`).
     - Window decoration colors (title bar, border, content background).
   - Window Manager (`WindowManager`):
     - Window creation, destruction, focus switching, and bring-to-front reordering.
     - Window translation (`wm_move_window`) and resizing (`wm_resize_window`).
     - Spatial hit-testing (`wm_hit_test`) returning the topmost visible window under cursor coordinates.

4. **Interactive Shell Integration (`os/kernel/kernel.asm`)**:
   - Shell command `gui` displaying graphics subsystem resolution, pitch, and mouse status.

5. **Automated Test Suite (`tests/test_os_graphics_mouse.py`)**:
   - Resolution initialization, pitch calculation, double buffering swap.
   - Clipping boundary enforcement on pixels, lines, and rectangles.
   - Bresenham line rasterization accuracy across diagonal, horizontal, and vertical vectors.
   - Alpha channel blend color math.
   - Bitmap font glyph and string rasterization.
   - PS/2 packet decoding (negative deltas, sign extension, button presses, boundary clamping).
   - Window z-ordering, focus transitions, dirty regions, and hit-testing.

## Technical Architecture

### 1. Framebuffer Structure
```kale
struct ClipRect {
    int32 x1;
    int32 y1;
    int32 x2;
    int32 y2;
}

struct Framebuffer {
    uint32* base_address;
    uint32* back_buffer;
    uint32 width;
    uint32 height;
    uint32 pitch; // bytes per line
    ClipRect clip;
    bool double_buffered;
}
```

### 2. PS/2 Mouse Packet Format (3 Bytes)
- **Byte 1**: `[Y_Ovf | X_Ovf | Y_Sign | X_Sign | Always1 | MiddleBtn | RightBtn | LeftBtn]`
- **Byte 2**: `Delta X` (8-bit magnitude, combined with X_Sign for two's complement delta)
- **Byte 3**: `Delta Y` (8-bit magnitude, combined with Y_Sign for two's complement delta)

## Success Criteria
- ✅ Framebuffer driver manages resolutions, clipping rectangles, and double-buffer blits.
- ✅ Bresenham's line algorithm draws accurate lines in all octants.
- ✅ Alpha blending correctly computes channel compositing without integer overflow.
- ✅ 8x8 bitmap font renders readable ASCII glyphs.
- ✅ PS/2 mouse decodes relative motion, button clicks, and clamps to screen bounds.
- ✅ Window manager handles creation, focus, z-order reordering, and coordinate hit-testing.
- ✅ 100% test pass rate on graphics and mouse test suite.
- ✅ Bare metal kernel build succeeds cleanly.
