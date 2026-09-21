# apps/git_lens — Kale Git Lens

GPU-accelerated visual VCS history viewer built on `libs/framework` + `libs/ui`.

## Files

| File | Description |
|---|---|
| `main.kl` | App entry, three-column layout loop, keyboard + mouse input |
| `commit_graph.kl` | Scrollable commit DAG panel (hash, author, message, branch lines) |
| `branch_view.kl` | Branch list sidebar (HEAD indicator, tip hash) |
| `diff_viewer.kl` | Colored unified diff panel for selected commit |

## Layout

```
┌──────────────────────────────────────────────────────┐
│  Git Lens   <repo>        [R] Refresh [↑↓] [ESC]     │ ← header (36px)
├──────────┬──────────────────────┬────────────────────┤
│ BRANCHES │ ● a1b2c3d  author   │ --- a/file.kl      │
│ ● master │   First commit       │ +++ b/file.kl      │
│          │ ○ e4f5a6b  author   │ @@ -1,3 +1,4 @@    │
│          │   Second commit      │  context line       │
│          │                      │ +added line         │
│          │                      │ -removed line       │
└──────────┴──────────────────────┴────────────────────┘
  180px       ~45% of remaining        ~55% remaining
```

## Keyboard Controls

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate commits |
| `PgUp` / `PgDn` | Scroll graph & diff |
| `R` | Refresh from repository |
| `ESC` | Quit |
| Mouse click | Select commit or branch |

## Status
`v0.1.0` — Initial release.
