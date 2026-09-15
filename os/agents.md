# Bare-Metal OS & Microkernel (`os/`)

## Version
`0.0.1`

## Description
Bare-metal x86_64 operating system, bootloader, and microkernel written in Kale and assembly, demonstrating freestanding language execution.

## Status
Current status: 🔴 Not Started

## Dependencies
- Kale compiler (with freestanding / `-ffreestanding` bare-metal target)
- NASM assembler & GNU ld / lld linker
- QEMU / Bochs for emulation and testing

## Build Instructions
```bash
nasm -f bin os/boot/boot.asm -o bin/boot.bin
kale build os/kernel/main.kl --freestanding -o bin/kernel.bin
qemu-system-x86_64 -drive format=raw,file=bin/os.img
```

## Coding Conventions
- No standard library (`no_std` / freestanding mode).
- Strict hardware memory alignment and volatile memory writes.

## Short-term Milestones
- [ ] Implement Stage 1 MBR bootloader in assembly.
- [ ] Configure GDT and enter 64-bit Long Mode.
- [ ] Initialize Serial COM1 driver and VGA text mode buffer in Kale.
- [ ] Configure IDT and timer interrupts.

## Future Plans
Preemptive multitasking scheduler, SMP multicore initialization, VirtIO drivers, and userland syscall interface.
