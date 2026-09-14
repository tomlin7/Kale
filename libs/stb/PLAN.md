# stb Single-Header Media Bindings (`libs/stb`) Plan

## 1. Overview
`libs/stb` vendors Sean Barrett's public domain single-header C libraries for TrueType font rasterization (`stb_truetype.h`) and image decoding (`stb_image.h`), paired with native Kale FFI bindings.

---

## 2. Directory Layout & Compilation

```
libs/stb/
├── vendor/
│   ├── stb_truetype.h      # Font rasterizer
│   ├── stb_image.h         # PNG, JPEG, BMP decoder
│   └── stb_impl.c          # Instantiates implementation macros
├── truetype.kl             # Kale FFI for font inspection & rasterization
├── image.kl                # Kale FFI for loading image pixel buffers
└── PLAN.md
```

### 2.1 C Implementation Wrapper (`stb_impl.c`)
```c
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```
Pre-compiled into `stb_impl.o` via Clang, and linked directly with Kale binaries.

---

## 3. Kale Binding Interface

### 3.1 `truetype.kl`
- `stbtt_InitFont(info: void*, data: void*, offset: int32) -> int32`
- `stbtt_ScaleForPixelHeight(info: void*, pixels: float32) -> float32`
- `stbtt_GetFontVMetrics(info: void*, ascent: int32*, descent: int32*, lineGap: int32*)`
- `stbtt_GetCodepointBitmap(info: void*, scale_x: float32, scale_y: float32, codepoint: int32, width: int32*, height: int32*, xoff: int32*, yoff: int32*) -> void*`
- `stbtt_FreeBitmap(bitmap: void*, userdata: void*)`
- `stbtt_GetCodepointHMetrics(info: void*, codepoint: int32, advanceWidth: int32*, leftSideBearing: int32*)`

### 3.2 `image.kl`
- `stbi_load(filename: string, x: int32*, y: int32*, channels: int32*, desired: int32) -> void*`
- `stbi_load_from_memory(buffer: void*, len: int32, x: int32*, y: int32*, channels: int32*, desired: int32) -> void*`
- `stbi_image_free(data: void*)`
