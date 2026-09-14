# 2D Render Engine

## Version
`0.0.1`

## Description
GPU-accelerated 2D rendering engine built on OpenGL 3.3. Provides batched quad rendering, shader management, font rendering via stb_truetype texture atlas, and texture management.

## Status
Current status: 🟢 Complete

## Dependencies
- libs/gl
- libs/glfw
- libs/stb

## Build Instructions
Imported by `libs/ui` and apps. Link with `-LE:\kale\libs\glfw\lib -lglfw3 -LE:\kale\libs\stb\lib -lstb -lopengl32`.

## Coding Conventions
- OpenGL 3.3 Core Profile conventions
- PascalCase for renderer/shader structs, snake_case for functions

## Short-term Milestones
- [x] Implement shader compilation (`libs/render/shader.kl`)
- [x] Implement batched renderer (`libs/render/batch.kl`, dynamic VBO/EBO, ortho projection)
- [x] Implement font loading + texture atlas (`libs/render/font.kl`, dynamic glyph rasterization)
- [x] Verified native GPU render pipeline test (`examples/render_pipeline_smoke.kl`)

## Future Plans
Add image rendering, gradients, blur effects, compute shaders.
