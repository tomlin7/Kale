# tools/pkg Architecture Plan

## 1. Overview
Hermetic build coordinator and dependency resolver for Kale applications and libraries.

## 2. Modules
- `manifest.kl`: kale.toml manifest parser.
- `solver.kl`: Dependency version constraint solver.
- `builder.kl`: Monorepo build DAG orchestrator with caching.
- `main.kl`: CLI porcelain (`new`, `build`, `test`, `publish`).
