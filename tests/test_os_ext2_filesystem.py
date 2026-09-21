import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSExt2Filesystem(unittest.TestCase):
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

    def test_ext2_superblock_parsing(self):
        code = r"""
        import "os/kernel/ext2.kl" as ext2;

        uint8[1024] data;
        int i = 0;
        while (i < 1024) {
            data[i] = 0 as uint8;
            i = i + 1;
        }

        // Magic 0xEF53 at offset 56
        data[56] = 0x53 as uint8;
        data[57] = 0xEF as uint8;

        // Inodes count = 16384 (0x00004000) at offset 0
        data[0] = 0x00 as uint8;
        data[1] = 0x40 as uint8;

        // Blocks count = 65536 (0x00010000) at offset 4
        data[4] = 0x00 as uint8;
        data[5] = 0x00 as uint8;
        data[6] = 0x01 as uint8;

        // s_log_block_size = 2 (4096 byte blocks) at offset 24
        data[24] = 2 as uint8;

        // s_blocks_per_group = 8192 (0x00002000) at offset 32
        data[32] = 0x00 as uint8;
        data[33] = 0x20 as uint8;

        // s_inodes_per_group = 2048 (0x00000800) at offset 40
        data[40] = 0x00 as uint8;
        data[41] = 0x08 as uint8;

        ext2.Ext2Superblock sb;
        ext2.ext2_parse_superblock(&sb, &data[0]);

        if (!sb.is_valid) return 1;
        if (sb.s_magic != ext2.EXT2_MAGIC) return 2;
        if (sb.block_size != (4096 as uint32)) return 3;
        // Group count = 65536 / 8192 = 8
        if (sb.group_count != (8 as uint32)) return 4;
        if (sb.s_inodes_per_group != (2048 as uint32)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ext2_inode_group_and_index(self):
        code = r"""
        import "os/kernel/ext2.kl" as ext2;

        ext2.Ext2Superblock sb;
        sb.s_inodes_per_group = 2048 as uint32;

        // Inode 1 -> group 0, index 0
        if (ext2.ext2_get_group_for_inode(&sb, 1 as uint32) != (0 as uint32)) return 1;
        if (ext2.ext2_get_index_in_group(&sb, 1 as uint32) != (0 as uint32)) return 2;

        // Inode 2 (root inode) -> group 0, index 1
        if (ext2.ext2_get_group_for_inode(&sb, 2 as uint32) != (0 as uint32)) return 3;
        if (ext2.ext2_get_index_in_group(&sb, 2 as uint32) != (1 as uint32)) return 4;

        // Inode 2049 -> group 1, index 0
        if (ext2.ext2_get_group_for_inode(&sb, 2049 as uint32) != (1 as uint32)) return 5;
        if (ext2.ext2_get_index_in_group(&sb, 2049 as uint32) != (0 as uint32)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ext2_inode_block_and_offset(self):
        code = r"""
        import "os/kernel/ext2.kl" as ext2;

        ext2.Ext2Superblock sb;
        sb.block_size = 4096 as uint32;
        uint32 bg_inode_table = 100 as uint32;

        // Index 0 -> block 100, offset 0
        uint32 b0 = ext2.ext2_get_inode_block(&sb, bg_inode_table, 0 as uint32);
        uint32 o0 = ext2.ext2_get_inode_offset(&sb, 0 as uint32);
        if (b0 != (100 as uint32) || o0 != (0 as uint32)) return 1;

        // Index 32: 32 * 128 = 4096 bytes -> block 101, offset 0
        uint32 b32 = ext2.ext2_get_inode_block(&sb, bg_inode_table, 32 as uint32);
        uint32 o32 = ext2.ext2_get_inode_offset(&sb, 32 as uint32);
        if (b32 != (101 as uint32) || o32 != (0 as uint32)) return 2;

        // Index 33: 33 * 128 = 4224 bytes -> block 101, offset 128
        uint32 b33 = ext2.ext2_get_inode_block(&sb, bg_inode_table, 33 as uint32);
        uint32 o33 = ext2.ext2_get_inode_offset(&sb, 33 as uint32);
        if (b33 != (101 as uint32) || o33 != (128 as uint32)) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ext2_inode_structure_parsing(self):
        code = r"""
        import "os/kernel/ext2.kl" as ext2;

        uint8[128] raw_node;
        int i = 0;
        while (i < 128) {
            raw_node[i] = 0 as uint8;
            i = i + 1;
        }

        // i_mode = 0x41ED (Directory + 0755 permissions) at offset 0
        raw_node[0] = 0xED as uint8;
        raw_node[1] = 0x41 as uint8;

        // i_size = 4096 at offset 4
        raw_node[4] = 0x00 as uint8;
        raw_node[5] = 0x10 as uint8;

        // Direct block pointer 0 = 500 at offset 40
        raw_node[40] = 0xF4 as uint8;
        raw_node[41] = 0x01 as uint8;

        ext2.Ext2Inode node;
        ext2.ext2_parse_inode(&node, &raw_node[0]);

        if (!node.is_dir) return 1;
        if (node.is_reg) return 2;
        if (node.i_size != (4096 as uint32)) return 3;
        if (node.i_block[0] != (500 as uint32)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ext2_dirent_parsing(self):
        code = r"""
        import "os/kernel/ext2.kl" as ext2;

        uint8[32] raw_ent;
        int i = 0;
        while (i < 32) {
            raw_ent[i] = 0 as uint8;
            i = i + 1;
        }

        // inode = 2 (root inode) at offset 0
        raw_ent[0] = 2 as uint8;

        // rec_len = 12 at offset 4
        raw_ent[4] = 12 as uint8;

        // name_len = 1 at offset 6
        raw_ent[6] = 1 as uint8;

        // file_type = EXT2_FT_DIR (2) at offset 7
        raw_ent[7] = 2 as uint8;

        // name = "." (0x2E) at offset 8
        raw_ent[8] = 0x2E as uint8;

        ext2.Ext2DirEntry ent;
        ext2.ext2_parse_dirent(&ent, &raw_ent[0]);

        if (!ent.is_valid) return 1;
        if (ent.inode != (2 as uint32)) return 2;
        if (ent.rec_len != (12 as uint16)) return 3;
        if (ent.name_len != (1 as uint8)) return 4;
        if (ent.file_type != ext2.EXT2_FT_DIR) return 5;
        if (ent.name[0] != (0x2E as uint8) || ent.name[1] != (0 as uint8)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ext2_invalid_superblock_magic(self):
        code = r"""
        import "os/kernel/ext2.kl" as ext2;

        uint8[1024] data;
        // Invalid magic 0x1234
        data[56] = 0x34 as uint8;
        data[57] = 0x12 as uint8;

        ext2.Ext2Superblock sb;
        ext2.ext2_parse_superblock(&sb, &data[0]);

        if (sb.is_valid) return 1;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
