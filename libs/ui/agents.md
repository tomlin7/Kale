# UI (GPU-Accelerated)

## Version
`0.0.1`

## Description
GPU-accelerated immediate-mode UI widget toolkit. Built on libs/render (OpenGL). Provides buttons, text inputs, sliders, scrollbars, layout, and theming.

## Status
Current status: 🟢 Complete

## Dependencies
- libs/render
- libs/glfw
- libs/gl
- libs/stb

## Build Instructions
Imported via `import "libs/ui/..." as alias;`. Link with `-LE:\kale\libs\glfw\lib -lglfw3 -LE:\kale\libs\stb\lib -lstb -lopengl32`.

## Coding Conventions
- Immediate-mode UI design patterns
- PascalCase for widget and state structs, snake_case for functions

## Short-term Milestones
- [x] Implement UIContext (`libs/ui/ui.kl`)
- [x] Implement basic widgets (`libs/ui/widgets.kl`: panel, label, button, slider)
- [x] Implement dark/light themes (`libs/ui/theme.kl`)
- [x] Verified native immediate-mode UI gallery test (`examples/ui_toolkit_smoke.kl`)

## Future Plans
Full widget set, accessibility, animations, custom widget API.
