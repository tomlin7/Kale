# Kale OS Changelog

## [0.1.0-alpha] - Current
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

### Current Status
- Bare-metal microkernel prototype
- Text-mode shell interface
- No multitasking
- No filesystem
- No user space
- No network support

## [Unreleased]
### Planned
- Virtual Memory Manager (VMM) with 4-level paging
- Task scheduler with round-robin preemption
- Complete ISR framework
- System call interface
- User space support with ELF loader
- Heap allocator for kernel and user space
