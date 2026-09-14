# stb Libraries

## Version
`0.0.1`

## Description
Vendored stb single-header C libraries with Kale FFI bindings. Includes stb_truetype (font rasterization) and stb_image (image loading).

## Status
Current status: 🔴 Not Started

## Dependencies
- PythonKale compiler
- C compiler (for building stb .o files)

## Build Instructions
Compile `vendor/stb_impl.c` with clang, then link the `.o` file with Kale programs.

## Coding Conventions
- C wrappers provide a clean C ABI for Kale FFI
- Kale bindings match C wrapper signatures with idiomatic Kale abstractions

## Short-term Milestones
- [ ] Vendor headers
- [ ] Create stb_impl.c
- [ ] Write truetype.kl and image.kl bindings

## Future Plans
Add stb_image_write, stb_rect_pack for better atlas packing.
