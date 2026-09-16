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
- [x] Build and publish a boot information structure with E820/stage metadata.
- [ ] Link a freestanding kernel entry and consume the boot information structure.
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
- [x] Initramfs archive mount/read contract and `/init` loading surface.
- [x] Interactive kernel console command registry with `help`, `mem`, `ticks`, `ls`, `cat`,
      `mount` and `reboot`.
- [ ] Shell-compatible error/status reporting and serial command transcript.

### Networking and reliability

- [x] Packet buffer and loopback network device.
- [x] UDP loopback framing and checksum contract.
- [ ] ARP/IPv4 transport.
- [x] Kernel assertions and structured panic state.
- [x] Boot stage additive checksums and generated manifests.
- [ ] Deterministic subsystem tests plus QEMU smoke tests for every boot path.

## Current execution order

The first foundation tranche is now implemented and pushed. The next tranche
will turn the contracts into a linked freestanding kernel: pass `BootInfo` from
the loader, consume the E820 map in PMM, attach the ATA device to the block
layer, mount the generated FAT12 disk, and drive the console from IRQ-backed
keyboard input. Hardware-dependent pieces remain isolated behind the same
interfaces so they can be tested on the host before full linking.
