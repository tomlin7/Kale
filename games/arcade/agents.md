# games/arcade — 2D Physics & Vector Arcade

## Version
`0.1.0`

## Description
Pure native Kale vector arcade game demonstrating seamless inter-op between `libs/vg` (vector drawing rasterizer) and `libs/physics` (2D rigid-body dynamics and collisions).

## Status
🟢 Active

## Dependencies
- `libs/vg`: Vector geometry, Bresenham line rendering, midpoint circle rasterization, canvas management
- `libs/physics`: RigidBody, Vec2, World numerical integrator, impulse and AABB collision detection

## Verification
- Unit & Gameplay Tests: `kale run tests/test_arcade.kl`
- Standalone Demo: `kale run games/arcade/main.kl`
