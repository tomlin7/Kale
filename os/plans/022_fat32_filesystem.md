# Milestone 22: FAT32 File System Subsystem

## Overview
Implement a high-performance, bare-metal FAT32 filesystem driver for Kale OS. Integrates directly with the block storage layer (ATA and AHCI) to parse partition tables, read the BIOS Parameter Block (BPB), traverse File Allocation Table (FAT) cluster chains, unpack directory entries, and read/write files and directories.

## Technical Architecture
1. **BIOS Parameter Block (BPB) & Boot Sector**:
   - `bytes_per_sector`: Sector size (standard 512 bytes).
   - `sectors_per_cluster`: Cluster granularity (power of 2: 1, 2, 4, 8, 16, 32, 64).
   - `reserved_sectors`: Sectors preceding the first FAT (typically 32).
   - `num_fats`: Count of FAT structures on disk (usually 2).
   - `sectors_per_fat_32`: Total sectors occupied by one FAT copy.
   - `root_cluster`: Starting cluster of root directory (typically cluster 2).
   - `fs_info_sector`: Location of the FSInfo sector (typically sector 1).
   - Boot signature: `0xAA55` at bytes 510-511.
2. **Cluster Calculations & Addressing**:
   - `first_data_sector = reserved_sectors + (num_fats * sectors_per_fat_32)`.
   - `cluster_to_lba(cluster) = first_data_sector + ((cluster - 2) * sectors_per_cluster)`.
   - `fat_entry_lba(cluster) = reserved_sectors + ((cluster * 4) / bytes_per_sector)`.
   - `fat_entry_offset(cluster) = (cluster * 4) % bytes_per_sector`.
3. **FAT Entry Semantics**:
   - 32-bit FAT entries with upper 4 bits reserved (effective 28-bit cluster address).
   - `0x00000000`: Free / Unallocated cluster.
   - `0x00000002`..`0x0FFFFFEF`: Allocated cluster pointing to next cluster in file chain.
   - `0x0FFFFFF7`: Defective / Bad sector cluster.
   - `0x0FFFFFF8`..`0x0FFFFFFF`: End-Of-Cluster-Chain (EOF).
4. **Directory Table Entries (32 bytes)**:
   - Bytes 0-10: 8.3 filename representation (`DIR_Name`, 8 name bytes + 3 extension bytes, space-padded).
   - Byte 11: File attributes (`ATTR_READ_ONLY = 0x01`, `ATTR_HIDDEN = 0x02`, `ATTR_SYSTEM = 0x04`, `ATTR_VOLUME_ID = 0x08`, `ATTR_DIRECTORY = 0x10`, `ATTR_ARCHIVE = 0x20`, `ATTR_LONG_NAME = 0x0F`).
   - Bytes 20-21: High 16 bits of first cluster (`DIR_FstClusHI`).
   - Bytes 26-27: Low 16 bits of first cluster (`DIR_FstClusLO`).
   - Bytes 28-31: 32-bit file size in bytes (`DIR_FileSize`).
   - Entry markers: `0x00` denotes end of directory list; `0xE5` marks deleted entries.

## Deliverables
- `os/plans/022_fat32_filesystem.md`: Specification document.
- `os/kernel/fat32.kl`: Complete pure Kale FAT32 parser and cluster chain manager.
- `tests/test_os_fat32.py`: Test suite validating BPB decoding, cluster-to-LBA calculation, FAT cluster chaining, directory parsing, and filename normalization.
