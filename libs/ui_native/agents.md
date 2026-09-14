# UI Native (Win32 GDI)

## Version
`0.1.0`

## Description
Win32 GDI-based UI widget library. Provides geometry types, event abstraction, double-buffered canvas drawing, and basic widgets (labels, buttons, containers). Being superseded by libs/ui (GPU-accelerated). Modules include geom.kl, event.kl, canvas.kl, widgets/label.kl, widgets/button.kl, and widgets/container.kl.

## Status
Current status: 🟡 In Progress (will transition to maintenance)

## Dependencies
- packages/bindings/win32
- packages/std

## Build Instructions
Imported by Kale programs via `import "libs/ui_native/..." as alias;`

## Coding Conventions
- Widget structs use PascalCase
- All drawing goes through Canvas

## Short-term Milestones
- [ ] Stabilize current widgets
- [ ] Add text input widget

## Future Plans
Maintain for Win32-only scenarios, primary UI moves to GPU-accelerated libs/ui.
