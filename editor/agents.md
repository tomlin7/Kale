# Flagship Code Editor

## Version
`0.2.0`

## Description
Native code editor for Kale, built on `libs/framework` v2 and GPU-accelerated rendering (`libs/render`, `libs/gl`, `libs/glfw`, `libs/stb`). Features syntax highlighting, line numbers gutter, status bar, and a piece table text buffer running at 60+ FPS.

## Status
Current status: 🟢 Active (GPU Architecture Completed)

## Dependencies
- libs/framework
- libs/render
- libs/gl
- libs/glfw
- libs/stb
- packages/std
- packages/editor

## Build Instructions
`kale build editor/main.kl -o bin/kale_edit.exe -LE:\kale\libs\glfw\lib -lglfw3 -LE:\kale\libs\stb\lib -lstb -lopengl32`

## Coding Conventions
- PascalCase for editor state and UI component structs, snake_case for action functions
- Decoupled buffer, rendering, and event-handling architectures
- Dynamic quad batching with zero heap allocations during scrolling or typing

## Short-term Milestones
- [x] GLFW window & OpenGL 3.3 Core Profile context bootstrap
- [x] GPU text viewport rendering via dynamic glyph atlas
- [x] Syntax token coloring with per-vertex RGBA interpolation
- [x] Interactive gutter with line numbers and status bar
- [ ] Multi-line selection and mouse drag selection
- [ ] Command palette & fuzzy file opener (`editor/command_bar.kl`)
- [ ] Undo / Redo history tracking in piece table
- [ ] Search / Replace bar

## Future Plans
LSP integration, multiple buffer tabs, split viewports, terminal emulator integration.
