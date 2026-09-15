# Bare-Metal OS & Microkernel (`os/`) Plan

## 1. Overview
The `os/` tree houses the low-level operating system components written in Kale and x86_64 assembly. It demonstrates Kale running on bare-metal hardware without any host operating system or C runtime.

---

## 2. Directory Layout & Architecture

```
os/
├── boot/            # Stage 1 MBR & Stage 2 protected-to-long mode bootloader
│   ├── boot.asm     # Real mode (16-bit) -> Protected mode (32-bit) -> Long mode (64-bit)
│   └── linker.ld    # Memory layout script (loads kernel at 1MB or 2MB higher-half)
├── kernel/          # Microkernel core written in Kale
│   ├── main.kl      # Kernel entry point (kmain)
│   ├── gdt.kl       # Global Descriptor Table & TSS setup
│   ├── idt.kl       # Interrupt Descriptor Table & ISR dispatch
│   ├── pic.kl       # 8259 Programmable Interrupt Controller remapping
│   ├── pmm.kl       # Physical Memory Manager (bitmap frame allocator)
│   ├── vmm.kl       # Virtual Memory Manager (x86_64 4-level paging tables)
│   └── sched.kl     # Cooperative/preemptive task scheduler
├── drivers/         # Hardware abstraction drivers
│   ├── vga.kl       # VGA text mode buffer (0xB8000)
│   ├── serial.kl    # 16550 UART serial driver for debug logging (COM1)
│   ├── fb.kl        # Linear framebuffer driver (VESA / UEFI GOP)
│   └── kbd.kl       # PS/2 keyboard controller & scancode decoder
└── PLAN.md
```

---

## 3. Boot Pipeline
1. **Bootloader (`os/boot`)**:
   - BIOS loads MBR sector at `0x7C00`.
   - Enables A20 line, loads kernel sectors into RAM.
   - Sets up temporary page tables and identity maps lower 2MB.
   - Enters Long Mode (64-bit), jumps to `kmain()`.
2. **Kernel Initialization (`os/kernel/main.kl`)**:
   - Initializes Serial COM1 port for debugging output.
   - Installs GDT, IDT, and remaps PIC interrupts (0x20 - 0x2F).
   - Initializes physical page frame allocator from BIOS memory map.
   - Clears VGA screen / initializes GOP framebuffer.
   - Enables interrupts (`sti`) and enters idle loop.

## 4. Runnable milestones

- [x] Assemble a fixed 512-byte BIOS boot sector.
- [x] Boot the sector in QEMU and enter x86_64 long mode.
- [x] Provide a direct QEMU runner that avoids shell/file-association launchers.
- [ ] Add a disk-loading second stage and transfer control to a linked kernel image.
- [ ] Add a freestanding Kale linker/runtime profile.
