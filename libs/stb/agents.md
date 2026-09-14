# stb Libraries

## Version
`0.0.1`

## Description
Vendored stb single-header C libraries with Kale FFI bindings. Includes stb_truetype (font rasterization) and stb_image (image loading).

## Status
Current status: 🟢 Complete

## Dependencies
- PythonKale compiler
- C compiler (for building stb .o files)
- stb library archive (`libs/stb/lib/stb.lib`)

## Build Instructions
Link with `-LE:\kale\libs\stb\lib -lstb`.

## Coding Conventions
- C wrappers provide a clean C ABI for Kale FFI
- Kale bindings match C wrapper signatures with idiomatic Kale abstractions

## Short-term Milestones
- [x] Vendor headers (`stb_truetype.h`, `stb_image_write.h`)
- [x] Create `stb_impl.c` with C ABI wrappers
- [x] Write `truetype.kl` font metrics and glyph rasterizer bindings
- [x] Verified native font loading and glyph rasterization test (`examples/stb_font_smoke.kl`)

## Future Plans
Add stb_image_write, stb_rect_pack for better atlas packing.
