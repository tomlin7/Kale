# Editor Engine (Legacy / Vim-Style)

## Version
`0.2.0`

## Description
Lightweight Vim-inspired terminal-style code editor engine. Features modal editing (`NORMAL`, `INSERT`, `COMMAND`, `VISUAL`), Vim keybindings (`h`, `j`, `k`, `l`, `i`, `a`, `o`, `x`, `:`), command parsing (`:w`, `:q`, `:wq`), interactive statusline, line numbering, and syntax highlighting.

## Status
Current status: 🟢 Active (Vim-Style Terminal Editor Core)

## Dependencies
- packages/std
- packages/bindings/win32

## Build Instructions
`kale build packages/editor/editor.kl -o editor.exe`

## Coding Conventions
- Standard Kale conventions: `.kl` source files, snake_case functions, PascalCase structs
