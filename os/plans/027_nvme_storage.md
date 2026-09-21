# Milestone 27: NVMe Solid-State Storage Driver

## Overview
Implement the Non-Volatile Memory Express (NVMe 1.4) solid-state storage driver architecture for Kale OS. Leverages PCIe MMIO registers, 64-byte circular Submission Queues (SQ), 16-byte Completion Queues (CQ), and Physical Region Page (PRP) memory descriptors to deliver high-throughput, low-latency NVMe block storage.

## Technical Architecture
1. **NVMe Controller Registers (BAR0 MMIO)**:
   - `CAP` (`0x00`): Maximum Queue Entries Supported (`MQES`), Doorbell Stride (`DSTRD`), Command Sets (`CSS`).
   - `VS` (`0x08`): Version specification (`0x00010400` = NVMe 1.4).
   - `CC` (`0x14`): Controller Configuration (`EN = 1`, `IOSQES = 6` for 64B SQEs, `IOCQES = 4` for 16B CQEs).
   - `CSTS` (`0x1C`): Controller Status (`RDY = 1`).
   - `AQA` (`0x24`): Admin Queue Attributes (`ASQS`, `ACQS`).
   - `ASQ` (`0x28`) / `ACQ` (`0x30`): 64-bit page-aligned Admin Queue Base Addresses.
   - Doorbells: Located at `0x1000 + (2 * QID) * (4 << DSTRD)` for SQ Tail and `+ (4 << DSTRD)` for CQ Head.
2. **Command Submissions (SQE - 64 bytes)**:
   - Opcode, Command Identifier (`CID`), Namespace ID (`NSID`).
   - PRP1 (64-bit buffer physical address) and PRP2.
   - 64-bit Starting LBA (`CDW10` and `CDW11`).
   - Block Count (`CDW12`: bits 15:0, zero-based: 0 = 1 block).
3. **Completion Queue Processing (CQE - 16 bytes)**:
   - SQ Head pointer, SQ ID, Command ID (`CID`).
   - Status field: Phase bit `P` indicating new entries, and Status Code `SC` (0 = Success).
4. **NVM Command Set**:
   - `NVME_NVM_CMD_READ` (`0x02`): LBA block reading into host memory.
   - `NVME_NVM_CMD_WRITE` (`0x01`): Host memory to disk writing.
   - `NVME_ADMIN_CMD_IDENTIFY` (`0x06`): Namespace sizing and block size discovery.

## Deliverables
- `os/plans/027_nvme_storage.md`: Architecture specification.
- `os/drivers/nvme.kl`: Pure Kale NVMe controller, SQ/CQ queue pair manager, and PRP command dispatcher.
- `tests/test_os_nvme_storage.py`: Test suite validating controller configuration, doorbell address calculation, 64-byte SQE construction, 16-byte CQE phase verification, and LBA block addressing.
