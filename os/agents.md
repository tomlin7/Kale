# Bare-Metal OS & Microkernel (`os/`)

## Version
`0.0.1`

## Description
Bare-metal x86_64 operating system, bootloader, and microkernel written in Kale and assembly, demonstrating freestanding language execution.

## Status
Current status: 🟡 Boot, storage, memory, scheduling, and service foundations complete; freestanding kernel integration in progress

## Dependencies
- Kale compiler (with freestanding / `-ffreestanding` bare-metal target)
- NASM assembler & GNU ld / lld linker
- QEMU / Bochs for emulation and testing

## Build Instructions
```powershell
pwsh os/boot/build.ps1
pwsh os/boot/run-qemu.ps1
# Headless smoke test:
pwsh os/boot/run-qemu.ps1 -Display none
```

The bootable artifact loads an eight-sector stage-two payload at `0x8000`,
collects the BIOS E820 map, enters protected mode and long mode, and transfers
control to that payload. A companion FAT12 data disk is generated for the next
ATA/VFS integration milestone. The Kale kernel sources are the next freestanding
integration target; the host compiler does not yet expose a `--freestanding`
linker mode.

## Coding Conventions
- No standard library (`no_std` / freestanding mode).
- Strict hardware memory alignment and volatile memory writes.

## Short-term Milestones
- [x] Implement Stage 1 MBR bootloader in assembly.
- [x] Configure GDT, enter 64-bit Long Mode, and hand off to stage two.
- [ ] Initialize Serial COM1 driver and VGA text mode buffer in Kale.
- [ ] Configure IDT and timer interrupts.

## Future Plans
Preemptive multitasking scheduler, SMP multicore initialization, VirtIO drivers, and userland syscall interface.
