# OpenGL 3.3 Bindings

## Version
`0.0.1`

## Description
Kale FFI bindings for OpenGL 3.3 Core Profile. Includes both static legacy GL 1.1 functions and dynamic GL 3.3+ function pointer loading via glfwGetProcAddress.

## Status
Current status: 🔴 Not Started

## Dependencies
- libs/glfw
- opengl32 system library

## Build Instructions
Link with `-lopengl32`

## Coding Conventions
- Match OpenGL C API and standard GL types (GLuint, GLenum, etc.)
- Dynamic function pointer loading table with null checks

## Short-term Milestones
- [ ] Core GL functions
- [ ] Shader/buffer/texture bindings
- [ ] Function pointer loader

## Future Plans
Add compute shader support, GL 4.x extensions.
