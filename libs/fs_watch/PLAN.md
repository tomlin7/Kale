# libs/fs_watch Architecture Plan

## 1. Overview
Filesystem watching engine powering editor auto-refresh and development hot-reloading.

## 2. Core Modules
- `backend_win32.kl`: ReadDirectoryChangesW asynchronous completion ports.
- `debouncer.kl`: Burst event coalescing and timestamp filtering.
- `watcher.kl`: Recursive directory tree registry and user callback dispatch.
