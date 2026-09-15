
<table>
<tr>
<td width="70%" valign="top">

<div align="center">

# K A L E

A statically-typed compiled language with direct **LLVM 18 IR** emission,
stack-allocated data structures, zero garbage collection, and sub-millisecond graphics.
Built entirely in Kale.


```
  pip install kale-lang
```

[Website](https://tomlin7.github.io/Kale) &nbsp;&nbsp;·&nbsp;&nbsp; [PyPI](https://pypi.org/project/kale-lang/) &nbsp;&nbsp;·&nbsp;&nbsp; [Actions](https://github.com/tomlin7/Kale/actions)

```
  MIT License
```

</div>

</td>
<td width="30%" valign="top">
<img src="website/public/assets/kale_hero_classical.jpg" width="100%" />
</td>
</tr>
</table>

<br>

```
  toolchain
```

<table>
<tr>
<td width="34%">
<sub><b>Kale Compiler</b> · <a href="src/kale/">src/kale/</a><br>
LLVM 18 IR emitter, Pratt parser, binder, JIT &amp; AOT via Clang/LLD.<br>
<code>pip install kale-lang</code></sub>
</td>
<td width="34%">
<sub><b>packages/std</b> · <a href="packages/std/">packages/std/</a><br>
Standard library — collections, strings, I/O, memory, generics, text.</sub>
</td>
<td width="34%">
<sub><b>tools/pkg</b> · <a href="tools/pkg/">tools/pkg/</a><br>
<code>kale-pm</code> package manager &amp; manifest resolver.</sub>
</td>
</tr>
</table>

<br>

```
  apps
```

<table>
<tr>
<td width="50%">
<sub><b>Kale Editor</b> · <a href="editor/">editor/</a><br>
144 Hz GPU-accelerated code editor. Piece table buffer, dynamic font atlas,<br>sub-pixel glyph rendering, multi-cursor, lexical syntax highlighting.</sub>
</td>
<td width="50%">
<sub><b>Kale VCS</b> · <a href="vcs/">vcs/</a><br>
Distributed version control in pure Kale. SHA-1 engine, DAG object store,<br>binary staging index, two-way diff, porcelain CLI: init/add/commit/log.</sub>
</td>
</tr>
<tr>
<td width="50%">
<sub><b>apps/lsp</b> · <a href="apps/lsp/">apps/lsp/</a><br>
Language Server Protocol server for IDE integration and diagnostics.</sub>
</td>
<td width="50%">
<sub><b>apps/kv</b> · <a href="apps/kv/">apps/kv/</a><br>
High-performance key-value daemon.</sub>
</td>
</tr>
</table>

<br>

```
  libs/
```

<table>
<tr>
<td width="34%">
<sub><b>libs/render</b> · <a href="libs/render/">libs/render/</a><br>
2D GPU batch renderer. SDF rounded rects, dynamic stb_truetype font atlas,<br>65k-vertex batches, single draw call per frame.</sub>
</td>
<td width="34%">
<sub><b>libs/ui</b> · <a href="libs/ui/">libs/ui/</a><br>
Immediate-mode widget toolkit. Buttons, sliders, inputs, scrollers,<br>declarative flow layout, ID-hash interaction state.</sub>
</td>
<td width="34%">
<sub><b>libs/framework</b> · <a href="libs/framework/">libs/framework/</a><br>
App harness — GLFW3 window, OpenGL 3.3 context,<br>frame pacing, unified input dispatch.</sub>
</td>
</tr>
</table>

<table>
<tr>
<td width="25%"><sub><b>libs/net</b> · <a href="libs/net/">libs/net/</a><br>Raw sockets &amp; HTTP/1.1 engine.</sub></td>
<td width="25%"><sub><b>libs/web</b> · <a href="libs/web/">libs/web/</a><br>HTTP router &amp; JSON responder.</sub></td>
<td width="25%"><sub><b>libs/sql</b> · <a href="libs/sql/">libs/sql/</a><br>SQLite3 FFI bindings &amp; query builder.</sub></td>
<td width="25%"><sub><b>libs/tls</b> · <a href="libs/tls/">libs/tls/</a><br>TLS 1.3 client over raw sockets.</sub></td>
</tr>
<tr>
<td width="25%"><sub><b>libs/audio</b> · <a href="libs/audio/">libs/audio/</a><br>PCM audio playback &amp; mixer.</sub></td>
<td width="25%"><sub><b>libs/physics</b> · <a href="libs/physics/">libs/physics/</a><br>2D rigid body physics engine.</sub></td>
<td width="25%"><sub><b>libs/term</b> · <a href="libs/term/">libs/term/</a><br>ANSI terminal engine &amp; TUI widgets.</sub></td>
<td width="25%"><sub><b>libs/fs_watch</b> · <a href="libs/fs_watch/">libs/fs_watch/</a><br>Cross-platform filesystem watcher.</sub></td>
</tr>
</table>

<br>

```
  os/
```

<table>
<tr>
<td width="50%">
<sub><b>os/ (Kale OS)</b> · <a href="os/">os/</a><br>
Bare-metal x86_64 kernel. Multiboot loader, IDT dispatcher, 4KB paging,<br>direct linear framebuffer — no host OS dependencies.</sub>
</td>
<td width="50%">
<sub><b>sys/sysmon</b> · <a href="sys/sysmon/">sys/sysmon/</a><br>
Real-time system monitor &amp; diagnostics dashboard.</sub>
</td>
</tr>
</table>

<br>

```
  QUICK START
```

```bash
pip install kale-lang

kale run   examples/fibonacci.kl          # LLVM JIT — in-memory execution
kale build examples/fibonacci.kl -o fib   # AOT — native binary via Clang/LLD
kale check examples/fibonacci.kl          # typecheck only
kale dump-llvm examples/fibonacci.kl      # inspect generated LLVM IR
```

```bash
# from source
uv sync && uv run pytest                  # install deps + run ~60 tests
```

<br>

```
  packages/vscode-kale  ·  Syntax highlighting & snippets for VS Code
  website/              ·  Next.js project showcase  →  tomlin7.github.io/Kale
```

<sub>MIT License</sub>
