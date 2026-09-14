# Flagship Code Editor

## Version
`0.1.0`

## Description
Native code editor for Kale, built on libs/framework and libs/ui_native. Features syntax highlighting, line numbers, status bar, and a piece table buffer. Will migrate to GPU rendering.

## Status
Current status: 🟡 In Progress

## Dependencies
- libs/framework
- libs/ui_native
- packages/std
- packages/editor

## Build Instructions
`kale build apps/editor/main.kl -o bin/kale_edit.exe`

## Coding Conventions
- PascalCase for editor state and UI component structs, snake_case for action functions
- Decoupled buffer, rendering, and event-handling architectures

## Short-term Milestones
- [ ] File open/save
- [ ] Undo/redo
- [ ] Search/replace
- [ ] Multiple tabs

## Future Plans
Migrate to GPU-rendered UI, LSP integration, plugin system, terminal emulator.
