# Milestone 7: Filesystem Layer & Virtual File System (VFS)

## Overview
Implement an extensible Virtual File System (VFS) and storage subsystem for Kale OS. This introduces storage abstraction, inode/vnode architecture, file descriptors, directory hierarchies, file operations (`open`, `read`, `write`, `close`, `seek`, `stat`), and a concrete filesystem implementation (in-memory ramdisk / KaleFS) integrated into the kernel and user space system call interface.

## Current State
- Milestone 1: Virtual Memory Manager (4-level paging, page fault handling)
- Milestone 2: Task Scheduler (PCB, 8254 PIT, preemptive context switching)
- Milestone 3: Interrupt Framework (IDT, PIC, keyboard, timer, ISR stubs)
- Milestone 4: System Call Interface (INT 0x80 / SYSCALL dispatcher, stats table)
- Milestone 5: User Space Support (ELF64 binary loader, TSS, Ring 3 privilege transitions)
- Milestone 6: Heap Allocator (Kernel heap, segregated size classes, coalescing free, user-space heap)
- No filesystem abstraction or file descriptors
- Shell and user programs cannot persist, read, or write structured files

## Objectives
1. Implement Virtual File System (VFS) abstraction (`os/kernel/vfs.kl`):
   - `VFSNode` (inode/vnode) with node types: File, Directory, CharDevice, BlockDevice, Pipe
   - POSIX-style permission flags: Read, Write, Execute
   - Function pointer operation tables: `open`, `read`, `write`, `close`, `seek`, `readdir`, `finddir`
2. Implement File Descriptor Management:
   - System-wide file table and per-process file descriptor tables (0=stdin, 1=stdout, 2=stderr)
   - Allocation, duplication (`dup`/`dup2`), and cleanup on process termination
3. Concrete In-Memory Filesystem (Ramdisk / KaleFS):
   - Hierarchical directory tree (`/`, `/bin`, `/dev`, `/etc`, `/tmp`, `/usr`)
   - File creation, deletion, truncation, append, and binary/text read-write operations
   - Pre-populated rootfs with device nodes (`/dev/null`, `/dev/zero`, `/dev/serial`, `/dev/vga`) and executable binaries (`/bin/init`, `/bin/sh`)
4. ATA / IDE Disk Driver Stubs (`os/drivers/ata.kl`):
   - PIO mode sector read and sector write routines for secondary storage
5. System Call Integration:
   - Connect VFS to syscall handlers: `SYS_OPEN` (2), `SYS_CLOSE` (3), `SYS_READ` (0), `SYS_WRITE` (1), `SYS_LSEEK` (8), `SYS_STAT` (4)
6. User-Space Standard Library (`libc`) Enhancements (`os/userspace/libc/stdio.kl`):
   - High-level `fopen`, `fclose`, `fread`, `fwrite`, `fseek`, `ftell`
7. Interactive Shell Enhancements (`os/kernel/kernel.asm`):
   - Shell commands: `ls`, `cat`, `touch`, `write`, `stat`
8. Comprehensive Verification:
   - Automated unit & integration tests (`tests/test_os_filesystem.py`)

## Technical Architecture

### 1. VFS Node Definition
```kale
uint32 VFS_FILE        = 1 as uint32;
uint32 VFS_DIRECTORY   = 2 as uint32;
uint32 VFS_CHARDEVICE  = 3 as uint32;
uint32 VFS_BLOCKDEVICE = 4 as uint32;
uint32 VFS_PIPE        = 5 as uint32;

// File Access Mode Flags
uint32 O_RDONLY = 0 as uint32;
uint32 O_WRONLY = 1 as uint32;
uint32 O_RDWR   = 2 as uint32;
uint32 O_CREAT  = 64 as uint32;
uint32 O_TRUNC  = 512 as uint32;
uint32 O_APPEND = 1024 as uint32;

// Seek Modes
uint32 SEEK_SET = 0 as uint32;
uint32 SEEK_CUR = 1 as uint32;
uint32 SEEK_END = 2 as uint32;
```

### 2. Concrete Filesystem Layout & Mount Points
- `/`: Root directory
  - `dev/`: Character and block devices
    - `null`: Bit bucket (discards writes, immediate EOF on read)
    - `zero`: Supplies infinite null bytes on read
    - `serial`: COM1 UART serial interface
    - `vga`: Direct console output
  - `bin/`: User executable binaries
    - `init`: System initialization daemon
    - `sh`: Shell interpreter
  - `etc/`: Configuration files
  - `tmp/`: Temporary scratch memory

## Success Criteria
- ✅ Clean VFS interface with inode operations
- ✅ Working directory traversal and path resolution (`/dir/file`)
- ✅ File read/write/seek/truncation operations functional
- ✅ File descriptor tables correctly managed and isolated per process
- ✅ Device nodes (`/dev/null`, `/dev/zero`, `/dev/serial`) routed through VFS
- ✅ System call interface integrated with VFS operations
- ✅ 100% test pass rate on filesystem test suite
- ✅ Bare-metal build and QEMU boot verified
