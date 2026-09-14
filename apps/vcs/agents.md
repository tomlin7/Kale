# Distributed VCS

## Version
`0.0.1`

## Description
A Git-compatible distributed version control system written in Kale.

## Status
Current status: 🔴 Not Started

## Dependencies
- packages/std (fs, collections, text)
- libs/net (for push/pull)

## Build Instructions
`kale build apps/vcs/main.kl -o bin/kale_vcs.exe`

## Coding Conventions
- Standard Kale conventions: `.kl` source files, PascalCase structs, snake_case functions
- Content-addressable storage models and modular CLI command implementations

## Short-term Milestones
- [ ] Object store (blob/tree/commit)
- [ ] Index
- [ ] Basic commands (init, add, commit, log, diff)

## Future Plans
Branch merging, remote push/pull, forge integration.
