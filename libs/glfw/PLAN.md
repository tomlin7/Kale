# GLFW3 Windowing & Input Bindings (`libs/glfw`) Plan

## 1. Overview
`libs/glfw` provides foreign function interface (FFI) bindings for the GLFW3 C library, abstracting cross-platform desktop window creation, OpenGL/Vulkan context initialization, and hardware input polling.

---

## 2. Module Specifications

### 2.1 `libs/glfw/glfw.kl`
Core window and lifecycle methods:
- `glfwInit() -> int32`
- `glfwTerminate()`
- `glfwCreateWindow(width: int32, height: int32, title: string, monitor: void*, share: void*) -> void*`
- `glfwDestroyWindow(window: void*)`
- `glfwWindowShouldClose(window: void*) -> int32`
- `glfwPollEvents()`
- `glfwSwapBuffers(window: void*)`
- `glfwMakeContextCurrent(window: void*)`
- `glfwSwapInterval(interval: int32)`
- `glfwGetTime() -> float64`

### 2.2 `libs/glfw/input.kl`
Hardware input polling & callback bindings:
- `glfwGetKey(window: void*, key: int32) -> int32`
- `glfwGetMouseButton(window: void*, button: int32) -> int32`
- `glfwGetCursorPos(window: void*, xpos: float64*, ypos: float64*)`
- `glfwSetKeyCallback(window: void*, callback: void*) -> void*`
- `glfwSetCursorPosCallback(window: void*, callback: void*) -> void*`
- `glfwSetScrollCallback(window: void*, callback: void*) -> void*`

### 2.3 `libs/glfw/constants.kl`
All necessary GLFW enumeration constants:
- Key codes (`GLFW_KEY_A` through `GLFW_KEY_Z`, navigation keys, function keys).
- Mouse buttons (`GLFW_MOUSE_BUTTON_1` through `8`).
- Window hints (`GLFW_CONTEXT_VERSION_MAJOR`, `GLFW_OPENGL_CORE_PROFILE`, etc.).

---

## 3. Build & Linking Requirements
- Requires `glfw3.dll` or `glfw3.lib` in the library search path.
- Linked via `kale build ... -lglfw3`.
