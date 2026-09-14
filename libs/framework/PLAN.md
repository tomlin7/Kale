# Application Framework (`libs/framework`) Evolution Plan

## 1. Overview
`libs/framework` is the canonical application lifecycle harness for Kale desktop applications. It manages window creation, event dispatch, frame timing, and double-buffering.

---

## 2. Framework v1 vs v2 Architecture

### v1 (Current - Win32 GDI)
- Direct integration with Win32 `WNDCLASS` and `user32/gdi32`.
- Uses `CreateCompatibleDC` / `BitBlt` for double-buffering.
- Limited to Windows platform.

### v2 (Target - GLFW3 & GPU Pipeline)
- Backend abstraction over GLFW3 (`libs/glfw`).
- Context initialization for OpenGL 3.3 Core Profile (`libs/gl`).
- Event polling maps GLFW input callbacks directly into unified `Event` structs.
- Frame presentation executes via `glfwSwapBuffers`.
- Native high-precision `delta_time` calculation.

---

## 3. Public Interface Contract
```
struct AppConfig {
    string title;
    int32 width;
    int32 height;
    bool vsync;
}

struct App {
    void* window_handle;
    float64 last_frame_time;
    float64 delta_time;

    fn void init(config: AppConfig)
    fn bool poll_event(event: Event*)
    fn void present()
    fn void close()
    fn bool is_running() -> bool
}
```

---

## 4. Implementation Steps
- [ ] Implement GLFW backend initialization in `libs/framework/app.kl`.
- [ ] Connect input callbacks (keyboard, mouse, scroll, resize) to the internal event queue.
- [ ] Integrate with `libs/render/context.kl` to auto-resize viewports on window resize events.
