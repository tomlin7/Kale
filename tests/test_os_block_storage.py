import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSBlockStorage(unittest.TestCase):
    def run_kale_jit(self, code: str):
        st = SourceText(code)
        diag = DiagnosticBag()
        loader = ModuleLoader([os.path.abspath(".")], diag)
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parser errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Binder errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        llvm_mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        return jit.run_ir(str(llvm_mod))

    def test_ata_device_init(self):
        code = """
        import "os/drivers/ata.kl" as ata;

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);

        if (dev.io_base != ata.ATA_PRIMARY_IO || dev.ctrl_base != ata.ATA_PRIMARY_CTRL) {
            return 1;
        }
        if (dev.is_slave != (0 as uint8) || dev.is_present || dev.supports_lba48) {
            return 2;
        }
        if (dev.sector_size != (512 as uint32) || dev.total_sectors != (0 as uint64)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ata_drive_identification_parsing(self):
        code = """
        import "os/drivers/ata.kl" as ata;

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);

        uint16[256] ident;
        int i = 0;
        while (i < 256) {
            ident[i] = 0 as uint16;
            i = i + 1;
        }

        // Word 0: Device type (bit 15 = 0 ATA)
        ident[0] = 0x0040 as uint16;
        // Word 49: Capabilities (bit 9 = LBA supported)
        ident[49] = 0x0200 as uint16;
        // Word 83: Command set (bit 10 = 48-bit LBA supported)
        ident[83] = 0x0400 as uint16;
        // Words 60-61: 28-bit sector count (e.g. 2,000,000 sectors)
        ident[60] = 0x8480 as uint16;
        ident[61] = 0x001E as uint16;
        // Words 100-103: 48-bit sector count (e.g. 10,000,000 sectors)
        ident[100] = 0x9680 as uint16;
        ident[101] = 0x0098 as uint16;
        ident[102] = 0x0000 as uint16;
        ident[103] = 0x0000 as uint16;

        // Words 27-46: Model string "KALE DISK       " (byte-swapped: 'AK', 'EL', ' D', 'SI', 'K ')
        ident[27] = ((('A' as uint16) << 8) | ('K' as uint16));
        ident[28] = ((('E' as uint16) << 8) | ('L' as uint16));
        ident[29] = (((' ' as uint16) << 8) | (' ' as uint16));
        ident[30] = ((('I' as uint16) << 8) | ('D' as uint16));
        ident[31] = ((('K' as uint16) << 8) | ('S' as uint16));

        bool ok = ata.ata_parse_identity(&dev, &ident[0]);
        if (!ok) {
            return 1;
        }
        if (!dev.is_present || !dev.supports_lba48) {
            return 2;
        }
        if (dev.total_sectors != (10000000 as uint64)) {
            return 3;
        }
        if (dev.model_name[0] != ('K' as char) || dev.model_name[1] != ('A' as char) ||
            dev.model_name[2] != ('L' as char) || dev.model_name[3] != ('E' as char)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ata_lba28_read_write(self):
        code = """
        import "os/drivers/ata.kl" as ata;

        uint8[4096] storage;
        int i = 0;
        while (i < 4096) {
            storage[i] = 0 as uint8;
            i = i + 1;
        }

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 8 as uint64, "KALE_TEST_ATA", false);

        // Prepare write buffer for sector 2
        uint8[512] write_buf;
        i = 0;
        while (i < 512) {
            write_buf[i] = (i % 251) as uint8;
            i = i + 1;
        }

        bool w_ok = ata.ata_write_sector_lba28(&dev, 2 as uint32, &write_buf[0]);
        if (!w_ok || dev.write_count != (1 as uint64)) {
            return 1;
        }

        // Read back into separate buffer
        uint8[512] read_buf;
        i = 0;
        while (i < 512) {
            read_buf[i] = 0 as uint8;
            i = i + 1;
        }

        bool r_ok = ata.ata_read_sector_lba28(&dev, 2 as uint32, &read_buf[0]);
        if (!r_ok || dev.read_count != (1 as uint64)) {
            return 2;
        }

        // Verify content matches
        i = 0;
        while (i < 512) {
            if (read_buf[i] != write_buf[i]) {
                return 3;
            }
            i = i + 1;
        }

        // Test out of bounds rejection
        bool oob = ata.ata_read_sector_lba28(&dev, 100 as uint32, &read_buf[0]);
        if (oob) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ata_lba48_read_write(self):
        code = """
        import "os/drivers/ata.kl" as ata;

        uint8[2048] storage;
        int i = 0;
        while (i < 2048) {
            storage[i] = 0 as uint8;
            i = i + 1;
        }

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 4 as uint64, "KALE_LBA48", true);

        uint8[512] w_buf;
        i = 0;
        while (i < 512) {
            w_buf[i] = 0xAA as uint8;
            i = i + 1;
        }

        bool w_ok = ata.ata_write_sector_lba48(&dev, 3 as uint64, &w_buf[0]);
        if (!w_ok) {
            return 1;
        }

        uint8[512] r_buf;
        bool r_ok = ata.ata_read_sector_lba48(&dev, 3 as uint64, &r_buf[0]);
        if (!r_ok) {
            return 2;
        }

        if (r_buf[0] != (0xAA as uint8) || r_buf[511] != (0xAA as uint8)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ata_multi_sector_operations(self):
        code = """
        import "os/drivers/ata.kl" as ata;

        uint8[2048] storage;
        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 4 as uint64, "KALE_MULTI", false);

        uint8[1024] w_buf;
        int i = 0;
        while (i < 1024) {
            w_buf[i] = (i & 0xFF) as uint8;
            i = i + 1;
        }

        // Write 2 sectors starting at LBA 1
        bool ok = ata.ata_write_sectors(&dev, 1 as uint64, 2 as uint32, &w_buf[0]);
        if (!ok || dev.write_count != (2 as uint64)) {
            return 1;
        }

        uint8[1024] r_buf;
        ok = ata.ata_read_sectors(&dev, 1 as uint64, 2 as uint32, &r_buf[0]);
        if (!ok || dev.read_count != (2 as uint64)) {
            return 2;
        }

        i = 0;
        while (i < 1024) {
            if (r_buf[i] != w_buf[i]) {
                return 3;
            }
            i = i + 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_bio_buffer_cache_init_and_miss_hit(self):
        code = """
        import "os/drivers/ata.kl" as ata;
        import "os/kernel/bio.kl" as bio;

        uint8[4096] storage;
        int i = 0;
        while (i < 4096) {
            storage[i] = 0 as uint8;
            i = i + 1;
        }
        storage[512] = 0x42 as uint8; // Block 1 first byte

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 8 as uint64, "KALE_BIO", false);

        bio.BufCache cache;
        bio.bio_init(&cache, &dev);

        // 1. Initial read should be a cache miss
        bio.BufHeader* b1 = bio.bio_bread(&cache, 0 as uint32, 1 as uint64);
        if (b1 == null) {
            return 1;
        }
        if (cache.cache_misses != (1 as uint64) || cache.cache_hits != (0 as uint64)) {
            return 2;
        }
        if (b1->data[0] != (0x42 as uint8)) {
            return 3;
        }

        // Release reference
        bio.bio_brelse(&cache, b1);

        // 2. Second read should be a cache hit
        bio.BufHeader* b2 = bio.bio_bread(&cache, 0 as uint32, 1 as uint64);
        if (b2 != b1) {
            return 4; // Should return same cached buffer
        }
        if (cache.cache_hits != (1 as uint64)) {
            return 5;
        }

        bio.bio_brelse(&cache, b2);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_bio_dirty_writeback_and_flush(self):
        code = """
        import "os/drivers/ata.kl" as ata;
        import "os/kernel/bio.kl" as bio;

        uint8[4096] storage;
        int i = 0;
        while (i < 4096) {
            storage[i] = 0 as uint8;
            i = i + 1;
        }

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 8 as uint64, "KALE_BIO_DIRTY", false);

        bio.BufCache cache;
        bio.bio_init(&cache, &dev);

        bio.BufHeader* b = bio.bio_bread(&cache, 0 as uint32, 2 as uint64);
        if (b == null) {
            return 1;
        }

        // Modify buffer content and mark dirty
        b->data[0] = 0xDE as uint8;
        b->data[1] = 0xAD as uint8;
        bio.bio_bwrite(&cache, b);

        if ((b->flags & bio.B_DIRTY) == (0 as uint32)) {
            return 2;
        }
        // Storage should NOT be updated yet before flush
        if (storage[1024] != (0 as uint8)) {
            return 3;
        }

        // Flush buffer
        bool flushed = bio.bio_bflush(&cache, b);
        if (!flushed || cache.writebacks != (1 as uint64)) {
            return 4;
        }
        // Dirty bit must be cleared
        if ((b->flags & bio.B_DIRTY) != (0 as uint32)) {
            return 5;
        }
        // Storage must now contain the flushed data
        if (storage[1024] != (0xDE as uint8) || storage[1025] != (0xAD as uint8)) {
            return 6;
        }

        bio.bio_brelse(&cache, b);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_bio_lru_eviction(self):
        code = """
        import "os/drivers/ata.kl" as ata;
        import "os/kernel/bio.kl" as bio;

        uint8[16384] storage;
        int i = 0;
        while (i < 16384) {
            storage[i] = (i & 0xFF) as uint8;
            i = i + 1;
        }

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 32 as uint64, "KALE_LRU", false);

        bio.BufCache cache;
        bio.bio_init(&cache, &dev);

        // Fill all 16 buffer slots
        uint64 blk = 0 as uint64;
        while (blk < (16 as uint64)) {
            bio.BufHeader* b = bio.bio_bread(&cache, 0 as uint32, blk);
            if (b == null) {
                return 1;
            }
            bio.bio_brelse(&cache, b);
            blk = blk + (1 as uint64);
        }

        if (cache.cache_misses != (16 as uint64)) {
            return 2;
        }

        // Access block 0 again to make it recently used
        bio.BufHeader* b0 = bio.bio_bread(&cache, 0 as uint32, 0 as uint64);
        bio.bio_brelse(&cache, b0);
        if (cache.cache_hits != (1 as uint64)) {
            return 3;
        }

        // Now read block 16 - this must evict an LRU slot (block 1 should be evicted, not block 0)
        bio.BufHeader* b16 = bio.bio_bread(&cache, 0 as uint32, 16 as uint64);
        if (b16 == null) {
            return 4;
        }
        bio.bio_brelse(&cache, b16);

        // Block 0 should still be cached!
        bio.BufHeader* test_b0 = bio.bio_find(&cache, 0 as uint32, 0 as uint64);
        if (test_b0 == null) {
            return 5; // Block 0 should NOT have been evicted!
        }

        // Block 1 should have been evicted
        bio.BufHeader* test_b1 = bio.bio_find(&cache, 0 as uint32, 1 as uint64);
        if (test_b1 != null) {
            return 6; // Block 1 should have been evicted
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_block_device_and_mount(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode root;
        vfs.vfs_node_init(&root, "/", vfs.VFS_DIRECTORY, 1 as uint64);

        vfs.VFSNode dev_dir;
        vfs.vfs_create_dir(&root, &dev_dir, "dev", 2 as uint64);

        vfs.VFSNode mnt_dir;
        vfs.vfs_create_dir(&root, &mnt_dir, "mnt", 3 as uint64);

        uint8[1024] disk_data;
        int i = 0;
        while (i < 1024) {
            disk_data[i] = 0 as uint8;
            i = i + 1;
        }

        // Create /dev/hda
        vfs.VFSNode hda;
        bool dev_ok = vfs.vfs_create_block_device(&dev_dir, &hda, "hda", &disk_data[0], 1024 as uint64, 4 as uint64);
        if (!dev_ok || hda.node_type != vfs.VFS_BLOCKDEVICE) {
            return 1;
        }

        // Open /dev/hda via file table
        vfs.FileTable table;
        vfs.vfs_file_table_init(&table);

        VFSNode* resolved_hda = vfs.vfs_resolve_path(&root, "/dev/hda");
        if (resolved_hda != &hda) {
            return 2;
        }

        int32 fd = vfs.vfs_open(&table, resolved_hda, vfs.O_RDWR);
        if (fd < 0) {
            return 3;
        }

        // Write to /dev/hda through VFS file descriptor
        uint8[4] test_write;
        test_write[0] = 0x55 as uint8;
        test_write[1] = 0xAA as uint8;
        test_write[2] = 0x12 as uint8;
        test_write[3] = 0x34 as uint8;

        int64 written = vfs.vfs_fd_write(&table, fd, &test_write[0], 4 as uint64);
        if (written != (4 as int64)) {
            return 4;
        }

        // Seek back to beginning
        vfs.vfs_fd_lseek(&table, fd, 0 as int64, vfs.SEEK_SET);

        // Read back
        uint8[4] test_read;
        int64 bytes_read = vfs.vfs_fd_read(&table, fd, &test_read[0], 4 as uint64);
        if (bytes_read != (4 as int64)) {
            return 5;
        }

        if (test_read[0] != (0x55 as uint8) || test_read[1] != (0xAA as uint8) ||
            test_read[2] != (0x12 as uint8) || test_read[3] != (0x34 as uint8)) {
            return 6;
        }

        // Mount /dev/hda onto /mnt
        bool mnt_ok = vfs.vfs_mount_block_device(&mnt_dir, &hda);
        if (!mnt_ok || mnt_dir.data != hda.data) {
            return 7;
        }

        vfs.vfs_close(&table, fd);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_bio_bflush_all(self):
        code = """
        import "os/drivers/ata.kl" as ata;
        import "os/kernel/bio.kl" as bio;

        uint8[4096] storage;
        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);
        ata.ata_setup_simulated_storage(&dev, &storage[0], 8 as uint64, "KALE_FLUSH_ALL", false);

        bio.BufCache cache;
        bio.bio_init(&cache, &dev);

        // Modify 3 blocks
        bio.BufHeader* b0 = bio.bio_bread(&cache, 0 as uint32, 0 as uint64);
        b0->data[0] = 11 as uint8;
        bio.bio_bwrite(&cache, b0);
        bio.bio_brelse(&cache, b0);

        bio.BufHeader* b1 = bio.bio_bread(&cache, 0 as uint32, 1 as uint64);
        b1->data[0] = 22 as uint8;
        bio.bio_bwrite(&cache, b1);
        bio.bio_brelse(&cache, b1);

        bio.BufHeader* b2 = bio.bio_bread(&cache, 0 as uint32, 2 as uint64);
        b2->data[0] = 33 as uint8;
        bio.bio_bwrite(&cache, b2);
        bio.bio_brelse(&cache, b2);

        uint32 flushed = bio.bio_bflush_all(&cache);
        if (flushed != (3 as uint32)) {
            return 1;
        }

        // Verify backing storage received the updates
        if (storage[0] != (11 as uint8) || storage[512] != (22 as uint8) || storage[1024] != (33 as uint8)) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ata_atapi_rejection(self):
        code = """
        import "os/drivers/ata.kl" as ata;

        ata.ATADevice dev;
        ata.ata_init(&dev, ata.ATA_PRIMARY_IO, ata.ATA_PRIMARY_CTRL, 0 as uint8);

        uint16[256] ident;
        ident[0] = 0x85C0 as uint16; // Bit 15 set -> ATAPI CD-ROM/device

        bool ok = ata.ata_parse_identity(&dev, &ident[0]);
        if (ok || dev.is_present) {
            return 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()

