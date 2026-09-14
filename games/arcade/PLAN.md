# games/arcade Architecture Plan

## 1. Overview
A high-performance, retro-futuristic 2D Vector & Physics Arcade game built natively in Kale. Leverages `libs/vg` for vector wireframe drawing and rasterization, and `libs/physics` for rigid-body collision, impulse resolution, and numerical dynamics.

## 2. Modules
- `entity.kl`: Entity state, entity archetypes (Player Ship, Asteroid/Target, Laser Projectile, Particle Spark), and geometry definitions.
- `game.kl`: Game state machine, simulation loop, physics world integration, collision response, score management, and vector rendering pipeline.
- `main.kl`: Standalone runnable arcade engine demonstration, automated simulation cycles, and gameplay verification.

## 3. Visual & Physics Specs
- Canvas resolution: 640x480 (or configurable).
- Pure vector aesthetics: wireframe ship geometry with damage feedback, midpoint circle asteroids, Bresenham laser strokes.
- Physics: Symplectic Euler integration, linear momentum, velocity damping, screen border restitution, and AABB collision resolution.
- Gameplay dynamics: 10-frame post-damage invulnerability buffer preventing immediate multi-drain death, with Game Over state taking strict priority over Victory.
