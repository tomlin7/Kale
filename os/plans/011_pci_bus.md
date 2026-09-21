# Milestone 11: PCI Device Enumeration & Bus Architecture

## Overview
Implement the Peripheral Component Interconnect (PCI) bus enumeration and device management framework for Kale OS. This subsystem allows the kernel to probe all PCI buses, discover hardware controllers (Ethernet, Storage, Audio, Display), decode Base Address Registers (BARs) for Memory-Mapped I/O (MMIO) and Port I/O, allocate interrupt resources, and automatically bind hardware drivers.

## Architecture

```
                       +-------------------------+
                       |    PCI Bus Manager      |
                       |    (os/drivers/pci.kl)  |
                       +------------+------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
     [Config Space]          [BAR Allocator]        [Driver Matcher]
    I/O 0x0CF8 / 0x0CFC     MMIO / Port I/O       RTL8139, E1000,
   32-bit dword access      Base & Size Probe     ATA, AC97, VGA
```

## Phases

### Phase 1: PCI Configuration Space Access
- Write 32-bit address to `0x0CF8`: `(1 << 31) | (bus << 16) | (device << 11) | (func << 8) | (reg & 0xFC)`.
- Read/Write 32-bit dword data via `0x0CFC`.
- Support 8-bit, 16-bit, and 32-bit configuration reads and writes with byte/word alignment and bit shifting.

### Phase 2: Device Iteration & Discovery
- Iterate through 256 buses, 32 devices per bus, and 8 functions per device.
- Read Vendor ID: `0xFFFF` indicates no device present.
- Detect multi-function devices via bit 7 of Header Type register (`0x0E`).
- Extract Device ID, Class Code, Subclass, Programming Interface (Prog IF), and Revision ID.

### Phase 3: Base Address Registers (BARs)
- Parse BAR0 through BAR5 in Header Type 0 (Standard Header):
  - Bit 0: `0` = Memory Space BAR, `1` = I/O Space BAR.
  - Memory Space:
    - Bits 2..1: `00` = 32-bit memory, `10` = 64-bit memory.
    - Bit 3: Prefetchable attribute.
    - Bits 31..4: Base address (16-byte aligned).
  - I/O Space:
    - Bits 31..2: Base address (4-byte aligned).
- Size probing: Save original BAR value, write `0xFFFFFFFF`, read back mask, compute size `(~(mask & (~0xF)) + 1)`, and restore original value.

### Phase 4: Command Register & Bus Mastering
- Enable device bus mastering (`PCI_CMD_BUS_MASTER = 0x0004`), memory space access (`0x0002`), and I/O space access (`0x0001`).
- Configure interrupt line and interrupt pin registers.

### Phase 5: Driver Binding & Device Registry
- Maintain array of discovered `PCIDevice` entries in kernel space.
- Device class matching:
  - Network: Class `0x02` (Subclass `0x00` Ethernet -> RTL8139 `0x10EC:0x8139`, E1000 `0x8086:0x100E`).
  - Mass Storage: Class `0x01` (Subclass `0x01` IDE / Subclass `0x06` SATA AHCI).
  - Display: Class `0x03` (Subclass `0x00` VGA -> Bochs `0x1234:0x1111`).
  - Multimedia Audio: Class `0x04` (Subclass `0x01` AC97 -> `0x8086:0x2415` / `0x8086:0x2445`).
