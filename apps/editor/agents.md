# apps/editor — Supercharged Code Editor & Terminal Split IDE

## Version
`0.3.0`

## Description
Flagship native Kale IDE application supercharged with multi-buffer tab management and embedded virtual terminal split powered by `libs/term` and `packages/std/text/piece_table.kl`.

## Status
🟢 Active (Terminal Split & Buffer Management Integrated)

## Dependencies
- `libs/term`: Virtual terminal emulator, ANSI escape parser, cell grid
- `packages/std`: piece table, string builder, collections
- `editor`: text viewport, gutter, status bar

## Verification
- Unit & Integration Tests: `kale run tests/test_editor_supercharged.kl`
- Standalone Harness: `kale run apps/editor/main.kl`
