# OpenGL 3.3 Bindings

## Version
`0.0.1`

## Description
Kale FFI bindings for OpenGL 3.3 Core Profile. Includes both static legacy GL 1.1 functions and dynamic GL 3.3+ function pointer loading via glfwGetProcAddress.

## Status
Current status: 🟢 Complete

## Dependencies
- libs/glfw
- opengl32 system library

## Build Instructions
Link with `-lopengl32 -LE:\kale\libs\glfw\lib -lglfw3`.

## Coding Conventions
- Match OpenGL C API and standard GL types (GLuint, GLenum, etc.)
- Dynamic function pointer loading table with null checks

## Short-term Milestones
- [x] Core GL functions (`libs/gl/gl.kl`, `libs/gl/constants.kl`)
- [x] Shader/buffer/texture bindings
- [x] Function pointer loader (`libs/gl/loader.kl`, `GLContext.load()`)
- [x] Verified native OpenGL 3.3 Core clear test (`examples/gl_clear_smoke.kl`)

## Future Plans
Add compute shader support, GL 4.x extensions.
