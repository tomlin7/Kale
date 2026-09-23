# Kale OS Changelog

## [0.2.0-alpha] - Current
### Added
- **Milestone 33**: Virtual Desktop Workspace Manager & Multi-Monitor Viewport (`os/kernel/workspace.kl`, `os/plans/033_virtual_workspaces.md`, `tests/test_os_workspaces.py`) supporting 4 virtual desktops, sticky windows, workspace carousel cycling, and multi-display window migration.
- **Milestone 34**: Desktop Audio Mixer & PCM Sound Server (`os/kernel/sound_server.kl`, `os/plans/034_audio_mixer.md`, `tests/test_os_audio_mixer.py`) supporting multi-channel audio mixing (Master, System, Media, SFX), per-channel volume attenuation, and saturating clipping [-32768, 32767].
- **Milestone 35**: System Settings Registry & Hardware Telemetry Subsystem (`os/kernel/settings.kl`, `os/plans/035_system_settings.md`, `tests/test_os_settings.py`) providing typed key-value configuration storage and real-time CPU/RAM/uptime performance sampling.
- **Milestone 36**: User-Space POSIX Runtime Library (`libkale` / `libc` ABI) (`os/userspace/libkale.kl`, `os/plans/036_userspace_runtime.md`, `tests/test_os_userspace_runtime.py`) featuring POSIX syscall wrappers, a 16-byte aligned dynamic memory allocator (`malloc`/`free`), and memory/string primitives.
- Complete Virtual Memory Manager (VMM) with 4-level paging
- Page table entry structures and manipulation functions
- Virtual address mapping and unmapping
- Address translation (virtual to physical)
- Memory layout definitions and validation
- Page fault handler with copy-on-write and demand paging
- Complete ISR framework with assembly stubs
- 32 CPU exception handlers (vectors 0-31)
- 16 hardware IRQ handlers (vectors 32-47)
- System call handler (vector 128)
- 64-bit ELF binary loader with header validation, program header parsing, and segment loading
- User space process management with address space isolation and PML4 setup
- SysV AMD64 ABI user stack frame setup at 0x00007FFFFFFFF000
- Ring 3 privilege transitions with TSS descriptor in GDT and iretq stack frames
- User CS (0x1B) and User SS (0x23) segment definitions with RPL 3
- User space standard library stubs and system call wrappers (libc stdio, stdlib, string, syscall)
- Kernel dynamic memory heap allocator (os/kernel/heap.kl) with first-fit allocation, 16-byte alignment, block splitting, and bi-directional coalescing
- AdvancedHeap segregated size classes (16, 32, 64, 128, 256, 512, 1024, 2048 bytes) for accelerated small allocation caching
- Dynamic memory reallocation (heap_realloc) supporting in-place growth, fragmentation splitting, and payload copying
- Dynamic memory zero-initialization (heap_calloc)
- Memory corruption detection and double-free mitigation via magic header validation (0x48454150)
- Memory leak detection and allocation metric counters (total allocations, total frees, peak usage, fragmentation ratio)
- Large allocation (> 64KB) dynamic mapping via page tables and physical frame allocation
- User-space process heap allocator (os/userspace/libc/heap.kl and stdlib.kl) with coalescing free and sbrk/brk syscall integration
- Enhanced interactive kernel shell with 'heap' command displaying live heap statistics and layout
- Enhanced kernel shell with 'user' command inspecting user space infrastructure
- Comprehensive user space support test suite with 100% pass rate
- Virtual File System (VFS) abstraction (`os/kernel/vfs.kl`) with inode/vnode architecture, permission modes, and node types (File, Directory, CharDevice, BlockDevice, Pipe)
- Hierarchical directory traversal and absolute path resolution (`/dir/subdir/file`)
- Process file descriptor table management (0=stdin, 1=stdout, 2=stderr) supporting open, close, and lowest-free FD allocation recycling
- File descriptor duplication via `vfs_dup` and `vfs_dup2`
- File seek capabilities (`SEEK_SET`, `SEEK_CUR`, `SEEK_END`) and node metadata queries (`vfs_stat_node`)
- Pre-populated rootfs with device nodes (`/dev/null`, `/dev/zero`, `/dev/serial`) and filesystem hierarchy (`/bin`, `/dev`, `/etc`, `/tmp`)
- System call dispatcher integration for `SYS_OPEN` (2) and `SYS_CLOSE` (3)
- User-space standard library stdio enhancements (`open`, `close`) in `os/userspace/libc/stdio.kl`
- Enhanced interactive kernel shell with 'ls' and 'cat' commands for directory inspection and file display
- Comprehensive Virtual File System test suite (`tests/test_os_filesystem.py`) with 100% pass rate
- ATA/IDE PIO mode hard disk driver (`os/drivers/ata.kl`) supporting primary/secondary bus ports (0x1F0-0x1F7), drive identification (0xEC), 28-bit LBA (0x20/0x30), and 48-bit LBA (0x24/0x34) sector read/write
- Block buffer cache (`os/kernel/bio.kl`) implementing LRU sector cache eviction, dirty buffer writeback, and hit/miss performance metrics
- Block storage VFS integration (`os/kernel/vfs.kl`) with `VFS_BLOCKDEVICE` node type, `/dev/hda` device creation, and partition mounting
- Comprehensive block storage test suite (`tests/test_os_block_storage.py`) with 14 automated unit tests covering drive identification, ATA register helpers, sector R/W, buffer cache LRU eviction, dirty writeback protection, and VFS block device mounting
- Framebuffer graphics driver (`os/drivers/fb.kl`) supporting 32-bit linear ARGB video modes (800x600, 1024x768), double buffering, and hardware scissor clipping
- 2D rasterization primitives: integer symmetric Bresenham line rendering across all octants, filled/outlined rectangles, ARGB alpha channel compositing, and expanded 8x8 monospace bitmap font typography
- PS/2 mouse hardware driver (`os/drivers/mouse.kl`) with 3-byte packet stream decoding, 9-bit sign extension, button state detection, and display boundary coordinate clamping
- Desktop window & canvas foundation (`os/kernel/window.kl`) with window descriptors, z-ordering, focus transitions, dirty region tracking, positive dimension bounds validation, and spatial hit-testing
- Comprehensive graphics and mouse test suite (`tests/test_os_graphics_mouse.py`) with 15 automated unit tests
- Network device interface and loopback driver (`os/drivers/net_loopback.kl`) supporting 127.0.0.1, MTU 1500, packet ring buffers, and device traffic counters
- PCI Ethernet hardware driver stubs for Realtek RTL8139 (`os/drivers/rtl8139.kl`) and Intel E1000 Gigabit (`os/drivers/e1000.kl`)
- TCP/IP protocol stack and packet parser (`os/kernel/net.kl`) implementing Ethernet II framing (0x0800 IPv4, 0x0806 ARP), ARP cache resolution & reply synthesis, IPv4 RFC 791 16-bit Internet checksum calculation, ICMP ping echo reply generator, UDP socket datagram delivery with MTU payload boundary validation and malformed packet rejection
- Network socket system call interface (`SYS_SOCKET`, `SYS_BIND`, `SYS_SENDTO`, `SYS_RECVFROM`) integrated into `os/kernel/syscall.kl`
- Comprehensive networking test suite (`tests/test_os_networking.py`) with 12 automated unit tests
- Enhanced interactive kernel shell with 'disk', 'gui', and 'net' commands

### Changed
- Enhanced kernel.asm with ISR integration
- Updated PIC configuration for timer and keyboard
- Added interrupt statistics tracking
- Implemented ring buffer for keyboard input
- Fixed Kale syntax issues in memory layout and page fault handlers

### Current Status
- Working virtual memory management
- Interrupt-driven I/O (keyboard, timer)
- Page fault handling infrastructure
- Comprehensive unit test coverage
- Progress toward multitasking foundation

## [0.1.0-alpha] - Previous
### Added
- 16-bit MBR bootloader with long mode transition
- Basic 64-bit kernel with interactive shell
- VGA text mode display driver
- PS/2 keyboard driver (polling)
- Serial port driver (COM1)
- 8259 PIC remapping
- Basic identity paging setup
- Physical memory manager (PMM) with bitmap allocator
- GDT and IDT structures
- Comprehensive development roadmap
- OS project restructure from sys/ to os/

## [Unreleased]
### Planned
- Task scheduler with round-robin preemption
- System call interface
- User space support with ELF loader
- Heap allocator for kernel and user space
- Timer driver (8254 PIT) completion
- Context switching implementation
