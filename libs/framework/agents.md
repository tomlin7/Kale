# Application Framework

## Version
`0.1.0`

## Description
Application bootstrap framework. Handles window creation, event loop, double-buffered rendering lifecycle, and frame timing. Currently Win32-based, will migrate to GLFW.

## Status
Current status: 🟡 In Progress

## Dependencies
- libs/ui_native
- packages/bindings/win32
- packages/std

## Build Instructions
Imported via `import "libs/framework/app.kl" as app;`

## Coding Conventions
- Standard Kale conventions: `.kl` files, PascalCase structs, snake_case functions
- Encapsulate platform lifecycle and event loops cleanly

## Short-term Milestones
- [ ] Migrate from Win32 to GLFW windowing
- [ ] Integrate GPU render context

## Future Plans
Become the canonical way to build Kale desktop applications.
