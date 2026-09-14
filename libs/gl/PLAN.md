# OpenGL 3.3 Core Profile Bindings & Loader (`libs/gl`) Plan

## 1. Overview
`libs/gl` exposes OpenGL 3.3 Core Profile functionality to Kale programs, providing static exports from `opengl32.dll` and dynamic extension loading via `glfwGetProcAddress`.

---

## 2. Architecture & Modules

### 2.1 Static Legacy Bindings (`gl.kl`)
Functions exported directly by standard operating system OpenGL drivers:
- `glClearColor(r: float32, g: float32, b: float32, a: float32)`
- `glClear(mask: int32)`
- `glViewport(x: int32, y: int32, width: int32, height: int32)`
- `glEnable(cap: int32)`, `glDisable(cap: int32)`
- `glBlendFunc(sfactor: int32, dfactor: int32)`
- `glScissor(x: int32, y: int32, width: int32, height: int32)`
- `glDrawArrays(mode: int32, first: int32, count: int32)`
- `glDrawElements(mode: int32, count: int32, type_: int32, indices: void*)`

### 2.2 Dynamic Core Extension Loader (`loader.kl`)
Function pointers loaded dynamically at runtime after context creation:
- **Shaders**: `glCreateShader`, `glShaderSource`, `glCompileShader`, `glCreateProgram`, `glAttachShader`, `glLinkProgram`, `glUseProgram`, `glDeleteShader`.
- **Buffers & VAOs**: `glGenVertexArrays`, `glBindVertexArray`, `glGenBuffers`, `glBindBuffer`, `glBufferData`, `glBufferSubData`.
- **Attributes & Uniforms**: `glVertexAttribPointer`, `glEnableVertexAttribArray`, `glGetUniformLocation`, `glUniformMatrix4fv`, `glUniform4f`.
- **Textures**: `glActiveTexture`, `glGenerateMipmap`.

### 2.3 Constants (`constants.kl`)
- Buffer targets (`GL_ARRAY_BUFFER`, `GL_ELEMENT_ARRAY_BUFFER`).
- Shader types (`GL_VERTEX_SHADER`, `GL_FRAGMENT_SHADER`).
- Primitive types (`GL_TRIANGLES`, `GL_LINES`, `GL_FLOAT`, `GL_UNSIGNED_INT`).
- Capabilities (`GL_BLEND`, `GL_SCISSOR_TEST`, `GL_SRC_ALPHA`, `GL_ONE_MINUS_SRC_ALPHA`).

---

## 3. Verification Plan
- Create a test application `examples/gl_triangle.kl` that loads functions, sets up a VAO, compiles a basic vertex/fragment shader, and renders a 2D colored triangle to the screen.
