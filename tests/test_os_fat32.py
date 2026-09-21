import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSFAT32(unittest.TestCase):
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

    def test_fat32_bpb_parsing_and_validation(self):
        code = r"""
        import "os/kernel/fat32.kl" as fat;

        uint8[512] sector;
        int i = 0;
        while (i < 512) {
            sector[i] = 0 as uint8;
            i = i + 1;
        }

        // Bytes per sector = 512 (0x0200) at offset 11
        sector[11] = 0x00 as uint8;
        sector[12] = 0x02 as uint8;

        // Sectors per cluster = 8 at offset 13
        sector[13] = 8 as uint8;

        // Reserved sectors = 32 (0x0020) at offset 14
        sector[14] = 0x20 as uint8;
        sector[15] = 0x00 as uint8;

        // Num FATs = 2 at offset 16
        sector[16] = 2 as uint8;

        // Sectors per FAT 32 = 1000 (0x000003E8) at offset 36
        sector[36] = 0xE8 as uint8;
        sector[37] = 0x03 as uint8;
        sector[38] = 0x00 as uint8;
        sector[39] = 0x00 as uint8;

        // Root cluster = 2 at offset 44
        sector[44] = 2 as uint8;

        // Boot signature 0x55 0xAA at 510-511
        sector[510] = 0x55 as uint8;
        sector[511] = 0xAA as uint8;

        fat.FAT32BPB bpb;
        fat.fat32_parse_bpb(&bpb, &sector[0]);

        if (!bpb.is_valid) return 1;
        if (bpb.bytes_per_sector != (512 as uint16)) return 2;
        if (bpb.sectors_per_cluster != (8 as uint8)) return 3;
        if (bpb.reserved_sectors != (32 as uint16)) return 4;
        if (bpb.num_fats != (2 as uint8)) return 5;
        if (bpb.sectors_per_fat_32 != (1000 as uint32)) return 6;
        if (bpb.root_cluster != (2 as uint32)) return 7;

        // first_data_sector = 32 + (2 * 1000) = 2032
        if (bpb.first_data_sector != (2032 as uint32)) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_fat32_cluster_to_lba(self):
        code = r"""
        import "os/kernel/fat32.kl" as fat;

        fat.FAT32BPB bpb;
        bpb.first_data_sector = 2032 as uint32;
        bpb.sectors_per_cluster = 8 as uint8;

        // Cluster 2 is the very first data cluster -> LBA 2032
        uint32 lba2 = fat.fat32_cluster_to_lba(&bpb, 2 as uint32);
        if (lba2 != (2032 as uint32)) return 1;

        // Cluster 3 -> 2032 + 8 = 2040
        uint32 lba3 = fat.fat32_cluster_to_lba(&bpb, 3 as uint32);
        if (lba3 != (2040 as uint32)) return 2;

        // Cluster 10 -> 2032 + (8 * 8) = 2096
        uint32 lba10 = fat.fat32_cluster_to_lba(&bpb, 10 as uint32);
        if (lba10 != (2096 as uint32)) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_fat32_fat_entry_lba_and_offset(self):
        code = r"""
        import "os/kernel/fat32.kl" as fat;

        fat.FAT32BPB bpb;
        bpb.reserved_sectors = 32 as uint16;
        bpb.bytes_per_sector = 512 as uint16;

        // Cluster 2 entry is at offset (2 * 4) = 8 bytes from FAT start
        // Sector = 32 + (8 / 512) = 32, offset = 8
        uint32 lba = fat.fat32_fat_entry_lba(&bpb, 2 as uint32);
        uint32 offset = fat.fat32_fat_entry_offset(&bpb, 2 as uint32);
        if (lba != (32 as uint32) || offset != (8 as uint32)) return 1;

        // Cluster 128 entry is at offset (128 * 4) = 512 bytes
        // Sector = 32 + (512 / 512) = 33, offset = 0
        uint32 lba128 = fat.fat32_fat_entry_lba(&bpb, 128 as uint32);
        uint32 off128 = fat.fat32_fat_entry_offset(&bpb, 128 as uint32);
        if (lba128 != (33 as uint32) || off128 != (0 as uint32)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_fat32_eof_detection(self):
        code = r"""
        import "os/kernel/fat32.kl" as fat;

        // 0x0FFFFFFF is EOF
        if (!fat.fat32_is_eof(0x0FFFFFFF as uint32)) return 1;

        // 0x0FFFFFF8 is minimum EOF marker
        if (!fat.fat32_is_eof(0x0FFFFFF8 as uint32)) return 2;

        // Mask upper 4 bits: 0xFFFFFFF8 should also be recognized as EOF
        if (!fat.fat32_is_eof(0xFFFFFFF8 as uint32)) return 3;

        // 0x0FFFFFF7 is bad cluster, not EOF
        if (fat.fat32_is_eof(0x0FFFFFF7 as uint32)) return 4;

        // 0x00000005 is regular cluster pointer, not EOF
        if (fat.fat32_is_eof(0x00000005 as uint32)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_fat32_format_83_name(self):
        code = r"""
        import "os/kernel/fat32.kl" as fat;

        // 1. "KERNEL  BIN" -> "KERNEL.BIN"
        uint8[11] raw_bin;
        raw_bin[0] = 75 as uint8; // 'K'
        raw_bin[1] = 69 as uint8; // 'E'
        raw_bin[2] = 82 as uint8; // 'R'
        raw_bin[3] = 78 as uint8; // 'N'
        raw_bin[4] = 69 as uint8; // 'E'
        raw_bin[5] = 76 as uint8; // 'L'
        raw_bin[6] = 32 as uint8; // ' '
        raw_bin[7] = 32 as uint8; // ' '
        raw_bin[8] = 66 as uint8; // 'B'
        raw_bin[9] = 73 as uint8; // 'I'
        raw_bin[10] = 78 as uint8;// 'N'

        uint8[13] formatted;
        fat.fat32_format_name(&raw_bin[0], &formatted[0]);

        // Should be 'K', 'E', 'R', 'N', 'E', 'L', '.', 'B', 'I', 'N', '\0'
        if (formatted[6] != (46 as uint8)) return 1; // '.'
        if (formatted[7] != (66 as uint8)) return 2; // 'B'
        if (formatted[10] != (0 as uint8)) return 3; // '\0'

        // 2. Directory without extension "SYS        " -> "SYS"
        uint8[11] raw_dir;
        raw_dir[0] = 83 as uint8; // 'S'
        raw_dir[1] = 89 as uint8; // 'Y'
        raw_dir[2] = 83 as uint8; // 'S'
        raw_dir[3] = 32 as uint8;
        raw_dir[4] = 32 as uint8;
        raw_dir[5] = 32 as uint8;
        raw_dir[6] = 32 as uint8;
        raw_dir[7] = 32 as uint8;
        raw_dir[8] = 32 as uint8;
        raw_dir[9] = 32 as uint8;
        raw_dir[10] = 32 as uint8;

        uint8[13] dir_fmt;
        fat.fat32_format_name(&raw_dir[0], &dir_fmt[0]);
        if (dir_fmt[3] != (0 as uint8)) return 4; // Null terminator right after 'S'

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_fat32_dirent_parsing(self):
        code = r"""
        import "os/kernel/fat32.kl" as fat;

        uint8[32] raw_ent;
        int i = 0;
        while (i < 32) {
            raw_ent[i] = 32 as uint8; // Space padding
            i = i + 1;
        }

        // Filename: "INIT    ELF"
        raw_ent[0] = 73 as uint8; // 'I'
        raw_ent[1] = 78 as uint8; // 'N'
        raw_ent[2] = 73 as uint8; // 'I'
        raw_ent[3] = 84 as uint8; // 'T'
        raw_ent[8] = 69 as uint8; // 'E'
        raw_ent[9] = 76 as uint8; // 'L'
        raw_ent[10] = 70 as uint8;// 'F'

        // Attribute: Archive (0x20)
        raw_ent[11] = 0x20 as uint8;

        // Cluster High = 0x0001 at offset 20
        raw_ent[20] = 0x01 as uint8;
        raw_ent[21] = 0x00 as uint8;

        // Cluster Low = 0x0004 at offset 26
        raw_ent[26] = 0x04 as uint8;
        raw_ent[27] = 0x00 as uint8;

        // File size = 4096 bytes (0x00001000) at offset 28
        raw_ent[28] = 0x00 as uint8;
        raw_ent[29] = 0x10 as uint8;
        raw_ent[30] = 0x00 as uint8;
        raw_ent[31] = 0x00 as uint8;

        fat.FAT32DirEntry ent;
        fat.fat32_parse_dirent(&ent, &raw_ent[0]);

        if (!ent.is_valid) return 1;
        if (ent.is_directory) return 2;
        // First cluster: (0x0001 << 16) | 0x0004 = 0x00010004 = 65540
        if (ent.first_cluster != (65540 as uint32)) return 3;
        if (ent.file_size != (4096 as uint32)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
