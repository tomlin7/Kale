# Milestone 12: ACPI & Power Management Subsystem

## Overview
Implement the Advanced Configuration and Power Interface (ACPI) subsystem for Kale OS. This milestone introduces physical memory scanning for the Root System Description Pointer (RSDP), parsing the Root System Description Table (RSDT), extracting power management controls from the Fixed ACPI Description Table (FADT / FACP), enabling hardware ACPI mode via SMI command ports, executing clean system shutdowns and reboots, and parsing the Multiple APIC Description Table (MADT) for CPU core topology.

## Architecture

```
                       +-------------------------+
                       |    ACPI Power Manager   |
                       |    (os/kernel/acpi.kl)  |
                       +------------+------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
     [RSDP Scanner]           [FADT Parser]           [MADT Parser]
   EBDA & BIOS ROM Area     PM1a_CNT / SMI_CMD      Local APIC & I/O APIC
    Checksum Validation      Poweroff & Reboot       CPU Core Discovery
```

## Phases

### Phase 1: RSDP & System Description Headers
- Scan Extended BIOS Data Area (EBDA: `0x9FC00..0x9FFFF`) and BIOS ROM area (`0x000E0000..0x000FFFFF`) on 16-byte boundaries for the 8-byte signature `"RSD PTR "`.
- Validate 20-byte checksum: all 20 bytes summed modulo 256 must equal 0.
- Parse standard `ACPISDTHeader`:
  - Signature (4 bytes, e.g. `"RSDT"`, `"FACP"`, `"APIC"`).
  - Length (32-bit dword).
  - Revision (8-bit byte).
  - Checksum (8-bit byte).
  - OEM ID (6 bytes) and OEM Table ID (8 bytes).

### Phase 2: RSDT / XSDT Table Pointer Extraction
- Extract array of 32-bit physical pointers from RSDT.
- Locate tables by matching signatures: `"FACP"` (FADT) and `"APIC"` (MADT).

### Phase 3: FADT & Power Management Registers
- Extract ACPI enable/disable parameters:
  - `smi_cmd`: System Management Interrupt command port (e.g. `0xB2` or `0x00B2`).
  - `acpi_enable` value: Command byte to write to `smi_cmd` to enable ACPI hardware mode.
  - `acpi_disable` value: Command byte to disable ACPI.
- Extract Power Management 1 Control Blocks:
  - `pm1a_cnt_blk`: Port I/O address for PM1a control register.
  - `pm1b_cnt_blk`: Optional PM1b control register port.
- Power Off (`S5` Sleep State):
  - Form `PM1_CNT` command: `(SLP_TYPa << 10) | SLP_EN (1 << 13: 0x2000)`.
  - Write to `pm1a_cnt_blk`. Fallback to QEMU/Bochs poweroff port `0x604` with data `0x2000` or port `0xB004` with data `0x2000`.
- System Reset / Reboot:
  - Check `FLAGS` in FADT (bit 10: `RESET_REG_SUP`).
  - Write `reset_value` to `reset_reg`. Fallback to 8042 keyboard controller reset command (`outb(0x64, 0xFE)`).

### Phase 4: MADT (Multiple APIC Description Table)
- Locate `"APIC"` table.
- Extract Local APIC physical address (default `0xFEE00000`) and APIC flags.
- Parse entry headers (Type `0` = Processor Local APIC, Type `1` = I/O APIC, Type `2` = Interrupt Source Override).
- Enumerate available CPU core IDs and enabled statuses for SMP preparation.
