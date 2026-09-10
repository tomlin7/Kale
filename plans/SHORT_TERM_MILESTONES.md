# Kale Short-Term Execution Milestones

This plan outlines the immediate, tactical sequence of phases designed to take us from our newly minted generics & collections foundation to an operable text buffer, filesystem pipeline, and GUI bootstrap.

---

## 📍 Phase 21: Enhanced File & Directory Systems (`packages/std/fs/`)
*Current Focus*

### Objectives:
1. **Path Handling (`std/fs/path.kl`)**:
   - `Path` struct / utility functions: `join`, `dirname`, `basename`, `ext`, `is_absolute`, `normalize`.
   - Cross-platform delimiter handling (`\` on Windows, `/` on POSIX).
2. **Directory & Metadata Operations (`std/fs/dir.kl`)**:
   - C runtime bindings for directory operations: `opendir`/`readdir`/`closedir` or `_findfirst`/`_findnext` via standard C bindings.
   - High-level directory iterator returning a `List<string>` of entries.
   - File status / metadata inspection: `exists`, `is_file`, `is_dir`, `file_size`.
3. **Tests**:
   - `tests/test_std_fs.py` testing file creation, path normalization, existence checks, and directory iteration in both LLVM JIT and C backends.

---

## 📍 Phase 22: High-Performance Text Buffer (`packages/std/text/`)

### Objectives:
1. **Piece Table / Line Gap Buffer (`std/text/piece_table.kl` or `buffer.kl`)**:
   - Original buffer (immutable file contents) + Add buffer (appended user inputs).
   - Node-based sequence of pieces tracking length, source buffer, and byte offset.
   - Constant-amortized insert and delete operations.
2. **Line & Offset Indexing**:
   - Line-to-offset and offset-to-line translations.
   - Text slice extraction (`get_line(idx: int): string`, `get_text(start: int, len: int): string`).
3. **Undo / Redo Stack**:
   - Command pattern or piece sequence history tracking undo and redo states with minimal memory copy.
4. **Tests**:
   - `tests/test_std_text.py` verifying multi-line document editing, arbitrary insertions/deletions, and line query consistency.

---

## 📍 Phase 23: Native Windowing & Event Loop Bootstrap

### Objectives:
1. **Windowing FFI Bindings (`packages/bindings/glfw/` or `sdl2/`)**:
   - Low-level header mapping for window initialization, swap buffers, polling events.
   - Keyboard events (keysym, modifiers, keyup/keydown) and mouse events (x, y, buttons, scroll).
2. **Event Dispatcher**:
   - Basic event loop abstraction in Kale: `Window::create(...)`, `Window::poll_events(...)`, `Window::is_open()`.
3. **Demo**:
   - A runnable Kale script `examples/window_demo.kl` opening a native desktop window and responding to keystrokes.

---

## 📍 Phase 24: 2D Graphics Canvas & Glyph Rendering

### Objectives:
1. **2D Graphics Integration**:
   - Hooking up OpenGL/DirectX/Software rasterizer or lightweight 2D C library (e.g. Raylib or NanoVG).
   - Primitives: rectangles, circles, lines, clipping masks.
2. **Font Rendering & Glyph Atlas**:
   - Monospace font rasterization for code display.
   - Texture atlas generation and quad batched rendering.

---

## 📍 Phase 25: The Kale Editor Core (v0.1 Prototype)

### Objectives:
1. Connecting `std/text` buffer to the 2D window renderer.
2. Handling keyboard navigation (arrow keys, Backspace, Enter, typing).
3. Cursor rendering with blinking cadence and scrolling viewport.
4. Status bar showing file name, cursor row/col, and dirty state.
