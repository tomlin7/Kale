# Distributed VCS (`vcs`)

## Version
`0.1.0`

## Description
A Git-compatible distributed version control system written entirely in Kale. Features content-addressable SHA-1 object storage (Blob, Tree, Commit), a binary/text staging area index (.kale/index), HEAD reference tracking, line difference analysis, and porcelain commands (init, add, commit, status, log, diff).

## Status
Current status: 🟢 Active (Stable v0.1.0)

## Dependencies
- `packages/std` (fs, collections, text)

## Build Instructions
```powershell
uv run kale build vcs/main.kl -o bin/kale_vcs.exe
```

## Architecture & Subsystems
- `vcs/sha1.kl`: Pure Kale RFC 3174 compliant 160-bit cryptographic SHA-1 engine.
- `vcs/object.kl`: Content-addressable object store for Git Blobs, Trees, and Commits with fanout directory partitioning (`.kale/objects/xx/yyyy...`).
- `vcs/index.kl`: Staging area tracker (`.kale/index`) supporting record lookup, serialization, and deserialization.
- `vcs/diff.kl`: Difference engine producing unified diffs (`--- a/...`, `+++ b/...`).
- `vcs/repo.kl`: Repository discovery, configuration, and branch HEAD reference resolution.
- `vcs/porcelain.kl`: High-level command implementations (`init`, `add`, `commit`, `status`, `log`, `diff`).
- `vcs/main.kl`: CLI command dispatcher and parameter parser.

## Completed Milestones
- [x] Pure Kale SHA-1 implementation validated against known hash test vectors (`vcs/sha1.kl`)
- [x] Content-addressable object store: Blob, Tree, and Commit objects (`vcs/object.kl`)
- [x] Staging index serializer and deserializer (`vcs/index.kl`)
- [x] Unified line-by-line difference generator (`vcs/diff.kl`)
- [x] Repository lifecycle and HEAD reference resolution (`vcs/repo.kl`)
- [x] Porcelain CLI commands: init, add, commit, status, log, diff (`vcs/porcelain.kl`)
- [x] Standalone executable `bin/kale_vcs.exe` verified (`vcs/main.kl`)
- [x] Automated comprehensive smoke test suite (`examples/vcs_smoke.kl`)

## Future Plans
- 3-way merge engine and merge conflict marker generation (`vcs/merge.kl`)
- Branching and checkout (`branch`, `checkout`, `switch`)
- Remote protocol support over HTTP/TCP via `libs/net` (`fetch`, `push`, `pull`)
- Packfile generation and index-pack parsing
