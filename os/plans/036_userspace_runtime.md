# Milestone 36: User-Space POSIX Runtime Library (`libkale` / `libc` ABI)

## Overview
Implement a comprehensive user-space POSIX runtime library (`libkale`) in pure Kale. This library provides POSIX system call abstractions, a freestanding dynamic memory allocator (`malloc` / `free` / `realloc`), string and memory manipulation primitives (`memcpy`, `memset`, `strlen`, etc.), and user-space program startup/termination scaffolding.

## Key Components
1. **Low-Level Syscall Dispatcher**:
   - `syscall0` through `syscall6` abstractions dispatching via x86_64 `syscall` instruction or simulated kernel dispatcher.
   - Syscall numbers conforming to Linux/POSIX x86_64 ABI (`SYS_READ=0`, `SYS_WRITE=1`, `SYS_OPEN=2`, `SYS_CLOSE=3`, `SYS_MMAP=9`, `SYS_BRK=12`, `SYS_GETPID=39`, `SYS_SOCKET=41`, `SYS_EXIT=60`).
2. **User-Space Memory Allocator (`malloc` / `free`)**:
   - User-space heap manager tracking memory chunks.
   - Chunk header: `size`, `is_free`, `next` pointer.
   - 16-byte alignment guarantee for SIMD/SSE operations.
3. **Standard Memory & String Utilities**:
   - `k_memcpy(dest, src, count)`
   - `k_memset(dest, val, count)`
   - `k_memcmp(s1, s2, count)`
   - `k_strlen(str)`
   - `k_strcmp(s1, s2)`
   - `k_strcpy(dest, src)`
4. **POSIX File and Process Wrappers**:
   - `k_read`, `k_write`, `k_open`, `k_close`, `k_exit`, `k_getpid`, `k_yield`.
