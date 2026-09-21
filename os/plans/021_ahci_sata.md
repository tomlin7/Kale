# Milestone 21: AHCI / SATA Storage Controller Subsystem

## Overview
Advance Kale OS block storage from legacy PIO-mode ATA to Advanced Host Controller Interface (AHCI) 1.3 for Serial ATA (SATA) disks. AHCI operates via memory-mapped I/O (MMIO) and utilizes high-performance Direct Memory Access (DMA) Scatter/Gather Physical Region Descriptor Tables (PRDT), eliminating CPU-bound PIO sector polling.

## Technical Architecture
1. **Generic Host Control (GHC) Structure**:
   - Host Capabilities (`CAP`), Global Host Control (`GHC`), Interrupt Status (`IS`), Ports Implemented (`PI`), Version (`VS`).
   - AHCI Enable (`GHC_AE = 1 << 31`), Interrupt Enable (`GHC_IE = 1 << 1`), HBA Reset (`GHC_HR = 1 << 0`).
2. **Port Register Map (`HBA_PORT`)**:
   - Command List Base Address (`CLB`/`CLBU` 64-bit).
   - FIS Base Address (`FB`/`FBU` 64-bit).
   - Interrupt Status (`IS`) and Interrupt Enable (`IE`).
   - Command and Status (`CMD`): Start (`ST = 1 << 0`), Spin-Up Device (`SUD = 1 << 1`), FIS Receive Enable (`FRE = 1 << 4`), FIS Receive Running (`FR = 1 << 14`), Command List Running (`CR = 1 << 15`).
   - Task File Data (`TFD`): Busy (`TFD_BSY = 0x80`), Data Request (`TFD_DRQ = 0x08`), Error (`TFD_ERR = 0x01`).
   - Signature (`SIG`): SATA drive (`0x00000101`), ATAPI drive (`0xEB140101`), Enclosure (`0xC33C0101`), Port Multiplier (`0x96690101`).
   - SATA Status (`SSTS`): Device Detection (`DET = 0x03` present and established communication), Interface Power Management (`IPM = 0x01` active).
   - Command Issue (`CI`): 32-bit bitmask indicating which command slots are actively pending execution.
3. **Command List & Command Header (`HBA_CMD_HEADER`)**:
   - Flags: Command FIS Length in dwords (`CFL`), ATAPI (`A`), Write (`W`), Prefetchable (`P`), Reset (`R`), BIST (`B`), Clear Busy upon R_OK (`C`), Port Multiplier Port (`PMP`).
   - PRDT Length (`PRDTL`): Number of scatter/gather entries.
   - PRD Byte Count (`PRDBC`): Transferred byte count.
   - Command Table Base Address (`CTBA`/`CTBAU` 64-bit).
4. **Command Table & PRDT (`HBA_CMD_TBL`, `HBA_PRDT_ENTRY`)**:
   - Command FIS (`CFIS`): Register FIS - Host to Device (`FIS_TYPE_REG_H2D = 0x27`).
   - PRDT Entries: Data Base Address (`DBA`/`DBAU` 64-bit), Byte Count (`DBC` 22-bit, up to 4MB per entry), Interrupt on Completion (`IOC = 1 << 31`).
5. **SATA Command Dispatch**:
   - `ATA_CMD_IDENTIFY_DEVICE` (0xEC)
   - `ATA_CMD_READ_DMA_EXT` (0x25, 48-bit LBA)
   - `ATA_CMD_WRITE_DMA_EXT` (0x35, 48-bit LBA)
   - Port start, port stop, and command issue polling.

## Deliverables
- `os/plans/021_ahci_sata.md`: Architectural specification.
- `os/drivers/ahci.kl`: Pure Kale AHCI driver with memory-mapped register structs, FIS constructors, and DMA transfer dispatch.
- `tests/test_os_ahci_sata.py`: Test suite validating signature detection, PRDT calculation, FIS generation, command slot allocation, and error status decoding.
