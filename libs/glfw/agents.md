# GLFW3 Bindings

## Version
`0.0.1`

## Description
Kale FFI bindings for GLFW3 (windowing, input, OpenGL context creation). Provides extern declarations for the GLFW C API.

## Status
Current status: 🟢 Complete

## Dependencies
- PythonKale compiler (needs -l linker flag)
- glfw3 library (`libs/glfw/lib/glfw3.lib`)

## Build Instructions
Link with `-LE:\kale\libs\glfw\lib -lglfw3 -lopengl32`.

## Coding Conventions
- Extern declarations match C ABI exactly
- UPPER_SNAKE_CASE for constants, snake_case for FFI wrapper functions

## Short-term Milestones
- [x] Core window/context functions
- [x] Input callbacks
- [x] Key/mouse constants
- [x] Verified native smoke test `examples/glfw_window_smoke.kl`

## Future Plans
Wayland support, gamepad input, multiple windows.
