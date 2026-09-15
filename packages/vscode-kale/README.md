# vscode-kale

> Syntax highlighting, bracket matching, and IDE commands for the [Kale programming language](https://github.com/kale-lang/kale).

## Features

- **Syntax Highlighting** — Full TextMate grammar covering:
  - Keywords: `fn`, `struct`, `enum`, `extern`, `import`, `let`, `var`, `const`, `operator`
  - Control flow: `if`, `else`, `while`, `for`, `switch`, `case`, `return`, `break`, `continue`
  - Types: `int`, `float`, `double`, `string`, `bool`, `char`, `void`
  - Built-ins: `print`, `input`, `alloc`, `free`
  - Operators, pointers (`*`, `&`, `->`, `^`), string/char literals, comments

- **Bracket Matching** — Auto-close and match `{}`, `[]`, `()`

- **Comment Toggling** — `Ctrl+/` for line comments (`//`), `Shift+Alt+A` for block (`/* */`)

- **IDE Commands** (via Command Palette or right-click context menu):

  | Command | Description |
  |---|---|
  | `Kale: Run File` | Execute `.kl` file via JIT |
  | `Kale: Build File` | Compile to native binary |
  | `Kale: Check File (Type Check)` | Typecheck without compiling |
  | `Kale: Dump AST` | Print the parsed AST tree |
  | `Kale: Dump Tokens` | Print the scanned token stream |
  | `Kale: Dump LLVM IR` | Print generated LLVM IR |

- **Status Bar Item** — Shows `⚡ Kale` in the status bar when editing `.kl` files; clicking it runs the current file.

## Requirements

The Kale compiler must be installed and accessible. In the monorepo, the default command is `uv run kale`.

## Extension Settings

| Setting | Default | Description |
|---|---|---|
| `kale.executablePath` | `uv run kale` | Command to invoke the Kale compiler |
| `kale.showStatusBarItem` | `true` | Show/hide the Kale status bar item |

## Usage

1. Open any `.kl` file — syntax highlighting activates automatically.
2. Right-click → **Kale: Run File** to execute.
3. Use `Ctrl+Shift+P` → `Kale:` to access all commands.

## Building the Extension

```bash
cd packages/vscode-kale
npm install
npm run compile       # TypeScript → out/extension.js
npm run package       # → vscode-kale-0.1.0.vsix
```

Then install in VSCode:

```
Extensions panel → ⋯ → Install from VSIX...
```

## File Association

All `.kl` files are automatically associated with the `kale` language ID.

## License

MIT
