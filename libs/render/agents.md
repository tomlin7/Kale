# 2D Render Engine

## Version
`0.0.1`

## Description
GPU-accelerated 2D rendering engine built on OpenGL 3.3. Provides batched quad rendering, shader management, font rendering via stb_truetype texture atlas, and texture management.

## Status
Current status: 🔴 Not Started

## Dependencies
- libs/gl
- libs/glfw
- libs/stb

## Build Instructions
Imported by libs/ui and apps.

## Coding Conventions
- OpenGL 3.3 Core Profile conventions
- PascalCase for renderer/shader structs, snake_case for functions

## Short-term Milestones
- [ ] Implement shader compilation
- [ ] Implement batched renderer
- [ ] Implement font loading + texture atlas
- [ ] Implement rounded rectangles via SDF

## Future Plans
Add image rendering, gradients, blur effects, compute shaders.
