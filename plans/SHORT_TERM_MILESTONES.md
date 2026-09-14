# Kale Short-Term Execution Milestones

This document provides actionable, discrete milestones designed to be dispatched to individual subagents. Each milestone has explicit dependencies, technical deliverables, and verification criteria.

---

## Milestone Execution Matrix

| ID | Title | Assigned Role | Dependencies | Status |
|---|---|---|---|---|
| **M0** | Housekeeping & Monorepo Alignment | Architect | None | 🟢 Complete |
| **M1** | PythonKale Compiler Stabilization | Compiler Engineer | M0 | 🟢 Complete |
| **M2** | `libs/glfw` Windowing FFI Bindings | Systems Engineer | M1 | 🟢 Complete |
| **M3** | `libs/gl` OpenGL 3.3 Core FFI & Loader | Graphics Engineer | M2 | 🟢 Complete |
| **M4** | `libs/stb` stb_truetype & stb_image FFI | Systems Engineer | M1 | 🟢 Complete |
| **M5** | `libs/render` 2D Batched GPU Graphics & Font Engine | Graphics Engineer | M2, M3, M4 | 🟢 Complete |
| **M6** | `libs/ui` GPU Immediate-Mode Widget Toolkit | UI Engineer | M5 | 🟢 Complete |
| **M7** | `libs/framework` v2 GPU App Harness | Framework Engineer | M6 | 🟢 Complete |
| **M8** | `libs/net` Sockets & HTTP/1.1 Client/Server | Network Engineer | M1 | 🟡 Next Up |
| **M9** | `libs/web` Routing, Middleware & Templates | Web Engineer | M8 | 🔴 Not Started |
| **M10** | `libs/sql` SQLite3 Driver & Query Builder | Database Engineer | M1 | 🔴 Not Started |
| **M11** | `editor` v2 Flagship GPU Code Editor | Editor Engineer | M6, M7 | 🟢 Complete |
| **M12** | `vcs` Distributed Version Control Core | Systems Engineer | M1, M8 | 🔴 Not Started |
| **M13** | `apps/blog` Publishing Engine & CMS | Web Engineer | M9, M10 | 🔴 Not Started |
| **M14** | Self-Hosting Kale Compiler Bootstrap | Lead Compiler Engineer | All | 🔵 Long-Term |

---

## 📍 Milestone 0: Housekeeping & Monorepo Alignment (Completed)
- [x] Renamed `libs/ui/` to `libs/ui_native/` (Win32 GDI widgets).
- [x] Updated all import statements across `apps/editor/`, `examples/`, `libs/framework/`, and tests.
- [x] Initialized `agents.md` across all 17 subprojects with semver tracking.
- [x] Updated `docs/monorepo_architecture.md`.

---

## 📍 Milestone 1: PythonKale Compiler Stabilization
**Role**: Compiler Engineer  
**Prerequisites**: Milestone 0  
**Target Files**: `src/kale/binding/`, `src/kale/codegen/`, `src/kale/cli.py`

### Deliverables:
1. **Float Support**: Ensure `f32` and `f64` primitives are fully bound and emitted as `ir.FloatType()` and `ir.DoubleType()`. Essential for OpenGL coordinates and matrices.
2. **Linker Argument Passthrough**: Update `cli.py` and `compiler.py` to accept `-l<lib>` and `-L<dir>` arguments, passing them directly to Clang/LLD during final binary linking (e.g. `-lglfw3 -lopengl32 -lws2_32`).
3. **Struct-by-Value Returns**: Ensure functions returning struct values correctly load values onto the caller stack frame without invalid pointer bitcasts.
4. **Stack Array Literals**: Support `let arr = [1, 2, 3];` stack array allocation.
5. **Testing**: Add `tests/test_floats.py` and `tests/test_linker_args.py`.

---

## 📍 Milestone 2: `libs/glfw` Windowing & Input FFI
**Role**: Systems Engineer  
**Prerequisites**: Milestone 1  
**Target Files**: `libs/glfw/glfw.kl`, `libs/glfw/input.kl`, `libs/glfw/constants.kl`, `libs/glfw/PLAN.md`

### Deliverables:
1. Complete C ABI declarations for GLFW3: `glfwInit`, `glfwCreateWindow`, `glfwMakeContextCurrent`, `glfwSwapBuffers`, `glfwPollEvents`, `glfwWindowShouldClose`.
2. Input polling & callbacks: `glfwGetKey`, `glfwGetCursorPos`, `glfwSetKeyCallback`, `glfwSetScrollCallback`.
3. Constants for window hints (`GLFW_CONTEXT_VERSION_MAJOR`, `GLFW_OPENGL_CORE_PROFILE`) and key codes.
4. Smoke test: `examples/glfw_window_smoke.kl` compiling to `.exe` and displaying a window.

---

## 📍 Milestone 3: `libs/gl` OpenGL 3.3 Core FFI & Dynamic Loader
**Role**: Graphics Engineer  
**Prerequisites**: Milestone 2  
**Target Files**: `libs/gl/gl.kl`, `libs/gl/loader.kl`, `libs/gl/constants.kl`, `libs/gl/PLAN.md`

### Deliverables:
1. Static OpenGL 1.1 bindings from `opengl32.dll` (`glClearColor`, `glViewport`, `glDrawArrays`).
2. Runtime extension loader using `glfwGetProcAddress`: `glCreateShader`, `glCompileShader`, `glGenVertexArrays`, `glGenBuffers`, `glBufferData`, `glUniformMatrix4fv`.
3. GL enums: `GL_COLOR_BUFFER_BIT`, `GL_TRIANGLES`, `GL_ARRAY_BUFFER`, `GL_STATIC_DRAW`, etc.
4. Verification: OpenGL context initialization test displaying a colored clear screen.

---

## 📍 Milestone 4: `libs/stb` stb_truetype & stb_image FFI
**Role**: Systems Engineer  
**Prerequisites**: Milestone 1  
**Target Files**: `libs/stb/vendor/`, `libs/stb/truetype.kl`, `libs/stb/image.kl`, `libs/stb/PLAN.md`

### Deliverables:
1. Vendor `stb_truetype.h` and `stb_image.h` in `libs/stb/vendor/`.
2. Provide `libs/stb/vendor/stb_impl.c` pre-compiled or compiled during build step.
3. Kale FFI bindings for font metric inspection, glyph bitmap rasterization, and PNG/JPEG loading.

---

## 📍 Milestone 5: `libs/render` 2D Batched GPU Graphics & Font Engine
**Role**: Graphics Engineer  
**Prerequisites**: Milestones 2, 3, 4  
**Target Files**: `libs/render/` (`shader.kl`, `batch.kl`, `font.kl`, `texture.kl`, `math.kl`, `context.kl`)

### Deliverables:
1. Minimal Linear Algebra: `Vec2`, `Vec4`, `Mat4` with orthographic 2D projection matrix calculation.
2. Batched 2D Vertex Pipeline: Struct `Vertex2D { x, y, u, v, r, g, b, a }`.
3. Dynamic VBO/EBO buffer streaming with single draw-call flushes.
4. Dynamic Font Glyph Texture Atlas with UTF-8 rasterization caching.
5. Analytical Anti-Aliased rounded rectangle shader (SDF).

---

## 📍 Milestone 6: `libs/ui` GPU Immediate-Mode Widget Toolkit
**Role**: UI Engineer  
**Prerequisites**: Milestone 5  
**Target Files**: `libs/ui/` (`ui.kl`, `widgets.kl`, `layout.kl`, `theme.kl`, `clipboard.kl`)

### Deliverables:
1. Immediate-mode lifecycle: `ui_begin()`, `ui_end()`, event translation.
2. Core widgets: `ui_button`, `ui_label`, `ui_text_input`, `ui_slider`, `ui_scrollbar`, `ui_panel`.
3. Layout primitives: Row, Column, Padding, Auto-sizing boxes.
4. Standard dark/light themes.

---

## 📍 Milestone 7: `libs/framework` v2 GPU App Harness (Completed)
**Role**: Framework Engineer  
**Prerequisites**: Milestone 6  
**Target Files**: `libs/framework/app.kl`, `libs/framework/PLAN.md`

### Deliverables:
1. [x] GLFW window bootstrap with automatic OpenGL 3.3 context configuration.
2. [x] Unified 60 FPS event dispatch loop with sub-millisecond delta time tracking.
3. [x] Seamless integration with `libs/ui` immediate-mode context.

---

## 📍 Milestone 8: `libs/net` Sockets & HTTP/1.1
**Role**: Network Engineer  
**Prerequisites**: Milestone 1  
**Target Files**: `libs/net/` (`socket.kl`, `http.kl`, `server.kl`)

### Deliverables:
1. Winsock2 / Berkeley socket wrappers for non-blocking TCP streams.
2. Minimal HTTP/1.1 client supporting GET, POST, custom headers, and body streaming.
3. Lightweight single-threaded HTTP/1.1 server.

---

## 📍 Milestone 9: `libs/web` Web Framework
**Role**: Web Engineer  
**Prerequisites**: Milestone 8  
**Target Files**: `libs/web/` (`router.kl`, `request.kl`, `response.kl`, `template.kl`)

### Deliverables:
1. Parameterized URL router supporting routes like `/api/v1/users/:id`.
2. Request and Response objects with JSON/HTML body serialization.
3. Fast string-interpolating template engine.

---

## 📍 Milestone 10: `libs/sql` SQLite3 Driver & Query Builder
**Role**: Database Engineer  
**Prerequisites**: Milestone 1  
**Target Files**: `libs/sql/` (`sqlite.kl`, `query.kl`)

### Deliverables:
1. SQLite3 C bindings (`sqlite3_open`, `sqlite3_prepare_v2`, `sqlite3_step`, `sqlite3_finalize`).
2. Ergonomic `Database` struct supporting parameterized execution and record set iteration.

---

## 📍 Milestone 11: `editor` v2 Flagship GPU Code Editor (Completed)
**Role**: Editor Engineer  
**Prerequisites**: Milestones 6, 7  
**Target Files**: `editor/` (`main.kl`, `app_state.kl`, `text_viewport.kl`, `gutter.kl`, `status_bar.kl`)

### Deliverables:
1. [x] Ultra-responsive GPU text viewport rendering arbitrary sized documents via `PieceTable`.
2. [x] Syntax token coloring directly on vertex batches.
3. [x] Active line highlighting, smooth scrolling, cursor blinking, and interactive gutter.

---

## 📍 Milestone 12: `vcs` Distributed Version Control System
**Role**: Systems Engineer  
**Prerequisites**: Milestones 1, 8  
**Target Files**: `vcs/` (`repo.kl`, `object.kl`, `index.kl`, `diff.kl`, `main.kl`)

### Deliverables:
1. Content-addressable SHA-1 object storage for Blobs, Trees, and Commits.
2. Working directory index tracker and Myers diff implementation.
3. CLI commands: `init`, `add`, `commit`, `status`, `log`, `diff`.

---

## 📍 Milestone 13: `apps/blog` Self-Hosted Publishing Platform
**Role**: Fullstack Engineer  
**Prerequisites**: Milestones 9, 10  
**Target Files**: `apps/blog/` (`models.kl`, `controllers.kl`, `views.kl`, `main.kl`)

### Deliverables:
1. Markdown article rendering and persistence in SQLite.
2. Web UI for viewing and editing articles.
3. Fast HTTP serving via `libs/web`.

---

## 📍 Milestone 14: Self-Hosting Compiler Bootstrap
**Role**: Lead Compiler Engineer  
**Prerequisites**: All previous milestones  
**Target Files**: `packages/compiler/`

### Deliverables:
1. Lexer, Parser, AST, Binder, and LLVM Emitter rewritten completely in Kale.
2. PythonKale compiles KaleKale; KaleKale compiles itself identically (reproducible binary).
