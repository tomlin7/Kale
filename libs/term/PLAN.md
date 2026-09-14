# libs/term Architecture Plan

## 1. Overview
The terminal foundation library for TUI applications, REPLs, and embedded editor terminals.

## 2. Module Breakdown
- `escape.kl`: State-machine escape sequence tokenizer (CSI, OSC, DCS).
- `grid.kl`: 2D character cell matrix with foreground/background colors and style bits.
- `pty.kl`: Windows ConPTY / POSIX openpty process bridging.
- `term.kl`: High-level raw mode toggles, cursor positioning, and screen clearing.
