# Application Framework

## Version
`0.1.0`

## Description
Application bootstrap framework. Handles window creation, event loop, double-buffered rendering lifecycle, and frame timing. Currently Win32-based, will migrate to GLFW.

## Status
Current status: 🟢 Complete

## Dependencies
- libs/ui
- libs/render
- libs/glfw
- libs/gl
- libs/stb

## Build Instructions
Imported via `import "libs/framework/app.kl" as app;`. Link with `-LE:\kale\libs\glfw\lib -lglfw3 -LE:\kale\libs\stb\lib -lstb -lopengl32`.

## Coding Conventions
- Standard Kale conventions: `.kl` files, PascalCase structs, snake_case functions
- Encapsulate platform lifecycle and event loops cleanly

## Short-term Milestones
- [x] Migrate from Win32 to GLFW windowing (`libs/framework/app.kl`)
- [x] Integrate GPU render context and automatic viewport presentation
- [x] Unified 60 FPS event loop with `begin_frame()` and `end_frame()`
- [x] Verified native framework app test (`examples/framework_app_smoke.kl`)

## Future Plans
Become the canonical way to build Kale desktop applications.
