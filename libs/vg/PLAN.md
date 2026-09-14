# libs/vg Architecture Plan

## 1. Overview
High-quality 2D vector primitives for data visualization, diagrams, and custom UI controls.

## 2. Modules
- `path.kl`: MoveTo, LineTo, QuadTo, CubicTo path builder.
- `tessellator.kl`: Monotone polygon triangulation and stroke expansion.
- `canvas.kl`: Retained-state 2D drawing context with affine transformation matrix.
