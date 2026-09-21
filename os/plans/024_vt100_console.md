# Milestone 24: ANSI / VT100 Terminal Console Subsystem

## Overview
Implement a hardware-accelerated ANSI/VT100 terminal console engine for Kale OS. Bridges the Pseudo-Terminal (PTY) and Framebuffer graphics subsystems by parsing ANSI escape sequences, maintaining an in-memory character/attribute matrix, handling screen scrolling and cursor movement, and rendering styled text directly onto the desktop display.

## Technical Architecture
1. **Terminal Grid Matrix (`VT100Screen`)**:
   - Fixed matrix of `VT100Cell` (e.g., 80 columns x 25 rows = 2000 cells).
   - Cell fields: `ch` (ASCII character), `fg_color` (32-bit ARGB), `bg_color` (32-bit ARGB), `flags` (bold, underline, inverse).
   - Active cursor position: `cur_x` (0..79), `cur_y` (0..24), visible flag, and saved cursor coordinates `(saved_x, saved_y)`.
2. **Parser State Machine**:
   - `STATE_NORMAL`: Regular character output, line wrapping, newline, carriage return, tab, and backspace.
   - `STATE_ESC`: Handles ESC single-character commands (`\x1b[`, `\x1b7`, `\x1b8`, `\x1bc`).
   - `STATE_CSI`: Parses semicolon-delimited arguments (`\x1b[param1;param2...cmd`).
3. **CSI Command Dispatch**:
   - `H` / `f`: Cursor Position (`\x1b[row;colH`).
   - `A`: Cursor Up (`\x1b[nA`).
   - `B`: Cursor Down (`\x1b[nB`).
   - `C`: Cursor Forward (`\x1b[nC`).
   - `D`: Cursor Back (`\x1b[nD`).
   - `J`: Erase in Display (`\x1b[2J` clears screen and resets cursor).
   - `K`: Erase in Line (`\x1b[K` clears from cursor to end of line).
   - `m`: Select Graphic Rendition (SGR):
     - `0`: Reset styles and colors.
     - `1`: Bold, `4`: Underline, `7`: Reverse video.
     - `30..37`: ANSI Foreground (Black, Red, Green, Yellow, Blue, Magenta, Cyan, White).
     - `40..47`: ANSI Background.
     - `90..97`: High-intensity Foreground.
     - `100..107`: High-intensity Background.
4. **Scrolling & Framebuffer Integration**:
   - Hardware-independent line scrolling (shifting cell rows up by 1, clearing bottom row).
   - Rendering bridge to blit cells using 8x16 font glyph bitmaps onto 32-bit ARGB framebuffers.

## Deliverables
- `os/plans/024_vt100_console.md`: Technical specification.
- `os/kernel/vt100.kl`: Pure Kale VT100 terminal matrix, ANSI state machine, and SGR color parser.
- `tests/test_os_vt100_console.py`: Test suite validating cursor positioning, SGR color codes, scrolling, screen/line clearing, and text wrapping.
