# GLFW3 Bindings

## Version
`0.0.1`

## Description
Kale FFI bindings for GLFW3 (windowing, input, OpenGL context creation). Provides extern declarations for the GLFW C API.

## Status
Current status: 🔴 Not Started

## Dependencies
- PythonKale compiler (needs -l linker flag)
- glfw3 library

## Build Instructions
Link with `-lglfw3`. GLFW binary must be available on system.

## Coding Conventions
- Extern declarations match C ABI exactly
- UPPER_SNAKE_CASE for constants, snake_case for FFI wrapper functions

## Short-term Milestones
- [ ] Core window/context functions
- [ ] Input callbacks
- [ ] Key/mouse constants

## Future Plans
Wayland support, gamepad input, multiple windows.
