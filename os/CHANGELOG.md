# Kale OS Changelog

## [0.2.0-alpha] - Current
### Added
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
- Enhanced kernel shell with 'user' command inspecting user space infrastructure
- Comprehensive user space support test suite with 100% pass rate

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
