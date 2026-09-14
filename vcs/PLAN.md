# Distributed Version Control System (`vcs`) Plan

## 1. Overview
`vcs` is a Git-compatible distributed version control system written entirely in Kale. It implements content-addressable storage, tree traversal, commit history graphs, working tree diffing, and command-line porcelain.

---

## 2. Directory Layout & Subsystems

```
vcs/
├── object.kl        # Content-addressable storage: Blob, Tree, Commit, Tag (SHA-1 hashing)
├── index.kl         # Staging area reader/writer (.kale/index or .git/index binary format)
├── repo.kl          # Repository discovery, config parsing, and HEAD reference tracking
├── diff.kl          # Myers difference algorithm for line-by-line file diffs
├── merge.kl         # Three-way merge engine and conflict marker generation
├── porcelain.kl     # CLI commands: init, add, commit, status, log, diff, branch, checkout
├── main.kl          # CLI entry point and argument parsing
└── PLAN.md
```

---

## 3. Core Architecture & Algorithms

### 3.1 Content-Addressable Object Store
- Objects are identified by their 160-bit SHA-1 hash.
- Format: `[type] [size]\0[content]`, compressed with DEFLATE/zlib.
- Stored under `.kale/objects/xx/yyyy...` (or standard `.git/objects/`).

### 3.2 Myers Difference Algorithm (`diff.kl`)
- Computes the shortest edit script (SES) between two sequences of lines in $O(ND)$ time and space.
- Generates standard unified diff output (`--- a/file`, `+++ b/file`, `@@ -1,5 +1,5 @@`).

### 3.3 Plumbing & Porcelain Pipeline
1. `kale-vcs init [dir]`: Initializes `.kale/` directory structure, `HEAD` pointing to `refs/heads/master`.
2. `kale-vcs add <path>`: Hashes file content into blob object, updates index entries with mode, file size, SHA-1, and relative path.
3. `kale-vcs commit -m <message>`: Writes tree objects recursively from index, constructs commit object with author, timestamp, parent commit SHA, and tree SHA, and updates `refs/heads/master`.
4. `kale-vcs log`: Traverses parent commit hashes backward, printing commit history graph.
5. `kale-vcs status`: Compares working tree vs index (unstaged changes) and index vs HEAD commit (staged changes).
