# Milestone 25: Ext2 File System Subsystem

## Overview
Implement the Second Extended File System (Ext2) architecture for Kale OS. Ext2 provides Unix-style hierarchical filesystem capabilities with fixed-size block groups, superblocks, inode tables, direct and indirect block pointers, and directory entries, enabling native Linux filesystem compatibility.

## Technical Architecture
1. **Ext2 Superblock (1024 bytes at byte offset 1024 in partition)**:
   - `s_inodes_count`: Total number of inodes across filesystem.
   - `s_blocks_count`: Total number of blocks.
   - `s_r_blocks_count`: Reserved block count for superuser.
   - `s_free_blocks_count`: Number of unallocated blocks.
   - `s_free_inodes_count`: Number of unallocated inodes.
   - `s_first_data_block`: First data block (usually 1 for 1KB block size, 0 for >1KB).
   - `s_log_block_size`: Block size = `1024 << s_log_block_size` (e.g., 0 for 1024, 1 for 2048, 2 for 4096).
   - `s_blocks_per_group`: Blocks in each block group (typically 8192).
   - `s_inodes_per_group`: Inodes in each block group.
   - `s_magic`: Magic signature `0xEF53`.
   - `s_state`: Clean (1) or error (2).
2. **Block Group Descriptor Table (BGDT)**:
   - Located immediately following the Superblock.
   - `bg_block_bitmap`: Block ID of block allocation bitmap.
   - `bg_inode_bitmap`: Block ID of inode allocation bitmap.
   - `bg_inode_table`: Starting block ID of the inode table.
   - `bg_free_blocks_count`, `bg_free_inodes_count`, `bg_used_dirs_count`.
3. **Inode Structure (128 bytes)**:
   - `i_mode`: File type and permissions (directory `0x4000`, regular file `0x8000`, permissions `0777`).
   - `i_uid`: Owner User ID.
   - `i_size`: Lower 32 bits of file size in bytes.
   - `i_atime`, `i_ctime`, `i_mtime`, `i_dtime`: Timestamps.
   - `i_gid`: Owner Group ID.
   - `i_links_count`: Hard link count.
   - `i_blocks`: 512-byte sector count allocated.
   - `i_block[15]`: Block pointers:
     - Direct blocks: 0 to 11 (first 12 blocks).
     - Singly-indirect: block 12.
     - Doubly-indirect: block 13.
     - Triply-indirect: block 14.
4. **Directory Entries (`ext2_dir_entry_2`)**:
   - `inode`: 32-bit inode number (0 indicates unlinked / unused entry).
   - `rec_len`: Total 16-bit record length to advance to next entry.
   - `name_len`: 8-bit length of filename string.
   - `file_type`: 8-bit file type (1 = regular file, 2 = directory, 7 = symlink).
   - `name`: ASCII characters of name (not null-terminated, length determined by `name_len`).

## Deliverables
- `os/plans/025_ext2_filesystem.md`: Specification document.
- `os/kernel/ext2.kl`: Ext2 parser, block-group math, inode locator, and directory entry reader.
- `tests/test_os_ext2_filesystem.py`: Test suite validating Superblock magic (`0xEF53`), block-to-group calculation, inode-to-block location, block pointer traversal, and directory entry unpacking.
