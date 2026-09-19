# Bare-Metal OS & Microkernel (`os/`)

## Version
`0.1.0`

## Description
Bare-metal x86_64 operating system, bootloader, microkernel, and hardware drivers written in Kale and assembly, demonstrating freestanding language execution.

## Status
Current status: 🟡 In Progress

## Sub-projects
- `os/boot`: Stage 1 MBR & Stage 2 protected-to-long mode bootloader.
- `os/kernel`: Microkernel core (GDT, IDT, PIC, PMM, VMM, Scheduler).
- `os/drivers`: Hardware drivers (VGA, 16550 UART serial, PS/2 keyboard, framebuffer).

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

