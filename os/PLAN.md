# Kale OS: systems roadmap

This roadmap is ordered by dependency. Each checked item must have a source
implementation, a focused test, and a QEMU/build verification where hardware is
involved. The current BIOS path is deliberately kept runnable while the
freestanding Kale kernel is brought up beside it.

## Architecture

```
os/
├── boot/       BIOS stages, disk layout, linker and QEMU runner
├── kernel/     architecture-neutral kernel services and entry points
├── arch/x86/   GDT, IDT, PIC, PIT, paging, context and port I/O
├── drivers/    serial, VGA, framebuffer, keyboard, ATA, RTC, timer
├── fs/         block device, FAT12/16, VFS and initramfs
├── mm/         physical frames, heap and virtual memory
├── proc/       tasks, scheduler, system calls and user mode
├── net/        packet buffers, Ethernet and loopback
└── tests/      image, parser and deterministic subsystem fixtures
```

## Core milestones

### Boot and architecture

- [x] BIOS boot sector with retrying CHS stage-two load.
- [x] Protected mode, long mode, identity paging and stage-two handoff.
- [x] GDT/IDT setup, PIC remap, keyboard IRQ queue and COM1 diagnostics.
- [x] E820 memory-map discovery and reserved-region reporting contract.
- [x] Expand the stage-two loader capacity and collect the BIOS E820 map.
- [ ] Link a freestanding kernel entry and pass a boot information structure.
- [x] Exception classification and structured panic reporting contracts.

### Time and hardware

- [x] PIT channel-0 timer programming and monotonic tick counter.
- [x] RTC CMOS date/time reader with BCD conversion.
- [ ] PS/2 controller command path, scancode translation and keyboard console.
- [x] 16550 serial RX interrupt ring buffer contract.
- [x] ATA PIO identify/read/write block driver contract.
- [x] PCI configuration-space enumerator and device registry contract.

### Memory and processes

- [ ] Physical frame allocator driven by the E820 map.
- [x] Early kernel heap with aligned allocation and bounds guards.
- [ ] 4-level virtual-memory mapper with page-fault diagnostics.
- [x] Task structure and round-robin scheduler contract.
- [ ] User-mode transition, syscall ABI and process address spaces.

### Filesystem and userland

- [x] Generic block-device API contract.
- [x] FAT12 parser: BPB validation, cluster-chain traversal, 8.3 lookup,
      directory iteration, file reads and writes.
- [x] VFS mount/open/read/seek/close API.
- [ ] Initramfs format and `/init` loading.
- [x] Interactive kernel console command registry with `help`, `mem`, `ticks`, `ls`, `cat`,
      `mount` and `reboot`.
- [ ] Shell-compatible error/status reporting and serial command transcript.

### Networking and reliability

- [x] Packet buffer and loopback network device.
- [ ] ARP/IPv4/UDP loopback services.
- [ ] Kernel assertions, structured panic dump and boot stage checksums.
- [ ] Deterministic subsystem tests plus QEMU smoke tests for every boot path.

## Current execution order

The next implementation tranche delivers the first ten unchecked foundations:
E820 discovery, counted/checksummed stage-two loading, boot information handoff,
exception/panic gates, PIT ticks, RTC conversion, a generic block device,
FAT12 parsing, VFS operations, and an interactive console. Hardware-dependent
pieces remain isolated behind small interfaces so they can be tested on the host
before full freestanding linking is available.
