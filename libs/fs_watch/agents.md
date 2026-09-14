# libs/fs_watch — Filesystem Event Watcher

## Version
`0.1.0`

## Description
Cross-platform, low-latency filesystem change monitoring. Listens to OS kernel change handles (ReadDirectoryChangesW / inotify) with event debouncing and deduplication.

## Status
🟡 In Progress

## Dependencies
- `packages/bindings/win32`: kernel32 directory change APIs
- `packages/std`: collections, fs
