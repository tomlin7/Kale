# Changelog

All notable changes to the `vscode-kale` extension will be documented here.

## [0.1.0] - 2026-09-15

### Added
- Initial release
- Full TextMate grammar for `.kl` files:
  - Syntax highlighting for keywords, types, operators, literals, comments, strings
  - Pointer/dereference operators (`*`, `&`, `->`, `^`)
  - Function and struct name highlighting
  - Import path highlighting
  - Builtin function highlighting (`print`, `input`, `alloc`, `free`)
- Language configuration:
  - Bracket auto-close and matching for `{}`, `[]`, `()`
  - String/char auto-close
  - Comment toggling (`//` and `/* */`)
  - Indentation rules
- IDE Commands:
  - `Kale: Run File` — JIT execute current `.kl` file
  - `Kale: Build File` — Compile to native binary
  - `Kale: Check File (Type Check)` — Typecheck only
  - `Kale: Dump AST` — Print AST
  - `Kale: Dump Tokens` — Print token stream
  - `Kale: Dump LLVM IR` — Print LLVM IR
- Status bar item showing `⚡ Kale` when editing `.kl` files
- Context menu entries for Run/Build in editor and explorer
- `kale.executablePath` and `kale.showStatusBarItem` configuration settings
