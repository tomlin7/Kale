# libs/physics Architecture Plan

## 1. Overview
A fast, lightweight 2D rigid-body simulation engine written in pure Kale.

## 2. Modules
- `math2d.kl`: Vectors, matrices, transforms, and bounding boxes.
- `broadphase.kl`: Dynamic spatial hash grid for fast broadphase culling.
- `collision.kl`: GJK and EPA narrowphase contact generation.
- `world.kl`: Symplectic Euler integrator, velocity constraints, and contact solver.
