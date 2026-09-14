# 2D Batched GPU Render Engine (`libs/render`) Plan

## 1. Overview
`libs/render` is the core high-performance 2D graphics engine for Kale. It translates high-level drawing primitives (rectangles, rounded panels, text spans, lines, and textures) into aggressively batched vertex buffers rendered in single OpenGL draw calls.

---

## 2. Architecture & Subsystems

```
libs/render/
├── math.kl          # Vec2, Vec4, Mat4, 2D orthographic projection
├── context.kl       # RenderContext, viewport bounds, shader management
├── shader.kl        # GLSL vertex & fragment shaders (SDF rounded rects, font)
├── batch.kl         # BatchRenderer: dynamic VBO/EBO, vertex packing, flush
├── font.kl          # Font cache, dynamic texture atlas, text layout & metrics
├── texture.kl       # OpenGL texture uploading, binding, and sampling
└── PLAN.md
```

---

## 3. Key Data Structures & Pipelines

### 3.1 Vertex Layout (`batch.kl`)
Each vertex is packed into 32 bytes:
```
struct Vertex2D {
    float32 x;
    float32 y;
    float32 u;
    float32 v;
    float32 r;
    float32 g;
    float32 b;
    float32 a;
}
```

### 3.2 Dynamic Font Texture Atlas (`font.kl`)
- Rasterizes Unicode glyphs on demand using `libs/stb/truetype.kl`.
- Packs glyph bitmaps into a single 1024x1024 (or 2048x2048) alpha texture.
- Maintains `GlyphInfo { float32 u0, v0, u1, v1; int32 width, height, xoff, yoff, xadvance; }`.
- Caches measured string bounds to accelerate editor rendering.

### 3.3 Batched Draw Commands
- `push_quad(x, y, w, h, color)`
- `push_rounded_rect(x, y, w, h, radius, color)` (evaluated via fragment shader Signed Distance Field)
- `push_textured_quad(x, y, w, h, tex_id, u0, v0, u1, v1)`
- `draw_text(font, text, x, y, color)`
- `flush()` commits vertex/index arrays to GPU via `glBufferSubData` and issues `glDrawElements`.
