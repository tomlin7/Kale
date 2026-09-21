import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSDynamicLinking(unittest.TestCase):
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

    def test_dynlink_elf_hash_calculation(self):
        code = r"""
        import "os/kernel/dynlink.kl" as dyn;

        // Compute hash of "printf\0"
        uint8[8] s_printf;
        s_printf[0] = 112 as uint8; // 'p'
        s_printf[1] = 114 as uint8; // 'r'
        s_printf[2] = 105 as uint8; // 'i'
        s_printf[3] = 110 as uint8; // 'n'
        s_printf[4] = 116 as uint8; // 't'
        s_printf[5] = 102 as uint8; // 'f'
        s_printf[6] = 0 as uint8;

        uint32 h_printf = dyn.elf_hash(&s_printf[0]);
        // System V hash of "printf" is 0x077905a6 = 125371814
        if (h_printf != (125371814 as uint32)) return 1;

        // Compute hash of "exit\0"
        uint8[8] s_exit;
        s_exit[0] = 101 as uint8; // 'e'
        s_exit[1] = 120 as uint8; // 'x'
        s_exit[2] = 105 as uint8; // 'i'
        s_exit[3] = 116 as uint8; // 't'
        s_exit[4] = 0 as uint8;

        uint32 h_exit = dyn.elf_hash(&s_exit[0]);
        // System V hash of "exit" is 0x0006cf04 = 446212
        if (h_exit != (446212 as uint32)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dynlink_rela_info_packing(self):
        code = r"""
        import "os/kernel/dynlink.kl" as dyn;

        uint32 sym_idx = 42 as uint32;
        uint32 rel_type = dyn.R_X86_64_JUMP_SLOT;

        uint64 r_info = dyn.rela_make_info(sym_idx, rel_type);

        uint32 extracted_sym = dyn.rela_get_sym(r_info);
        uint32 extracted_type = dyn.rela_get_type(r_info);

        if (extracted_sym != (42 as uint32)) return 1;
        if (extracted_type != dyn.R_X86_64_JUMP_SLOT) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dynlink_parse_dynamic_tags(self):
        code = r"""
        import "os/kernel/dynlink.kl" as dyn;

        dyn.Elf64_Dyn[8] entries;
        // DT_STRTAB = 0x00401000
        entries[0].d_tag = dyn.DT_STRTAB;
        entries[0].d_val = 0x00401000 as uint64;

        // DT_SYMTAB = 0x00402000
        entries[1].d_tag = dyn.DT_SYMTAB;
        entries[1].d_val = 0x00402000 as uint64;

        // DT_RELA = 0x00403000
        entries[2].d_tag = dyn.DT_RELA;
        entries[2].d_val = 0x00403000 as uint64;

        // DT_RELASZ = 480
        entries[3].d_tag = dyn.DT_RELASZ;
        entries[3].d_val = 480 as uint64;

        // DT_NEEDED = 64 (offset into string table)
        entries[4].d_tag = dyn.DT_NEEDED;
        entries[4].d_val = 64 as uint64;

        // DT_NULL (terminator)
        entries[5].d_tag = dyn.DT_NULL;
        entries[5].d_val = 0 as uint64;

        dyn.DynLinkInfo info;
        dyn.dynlink_parse_dynamic(&info, &entries[0], 8);

        if (info.strtab != (0x00401000 as uint64)) return 1;
        if (info.symtab != (0x00402000 as uint64)) return 2;
        if (info.rela != (0x00403000 as uint64)) return 3;
        if (info.relasz != (480 as uint64)) return 4;
        if (info.needed_count != 1) return 5;
        if (info.needed_offsets[0] != (64 as uint64)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dynlink_reloc_relative(self):
        code = r"""
        import "os/kernel/dynlink.kl" as dyn;

        // R_X86_64_RELATIVE = Base (B) + Addend (A)
        // Library loaded at 0x00007FFFF7800000 with addend 0x1234
        uint64 base_addr = 0x00007FFFF7800000 as uint64;
        int64 addend = 0x1234 as int64;
        uint64 patch = 0x00007FFFF7805000 as uint64;

        uint64 val = dyn.dynlink_calc_reloc(dyn.R_X86_64_RELATIVE, base_addr, 0 as uint64, addend, patch);
        uint64 expected = 0x00007FFFF7801234 as uint64;

        if (val != expected) return 1;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dynlink_reloc_glob_dat_and_jump_slot(self):
        code = r"""
        import "os/kernel/dynlink.kl" as dyn;

        // R_X86_64_GLOB_DAT and R_X86_64_JUMP_SLOT write resolved symbol address S directly
        uint64 sym_addr = 0x00007FFFF7A05500 as uint64;

        uint64 v_glob = dyn.dynlink_calc_reloc(dyn.R_X86_64_GLOB_DAT, 0 as uint64, sym_addr, 0 as int64, 0 as uint64);
        if (v_glob != sym_addr) return 1;

        uint64 v_jump = dyn.dynlink_calc_reloc(dyn.R_X86_64_JUMP_SLOT, 0 as uint64, sym_addr, 0 as int64, 0 as uint64);
        if (v_jump != sym_addr) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dynlink_reloc_64_and_pc32(self):
        code = r"""
        import "os/kernel/dynlink.kl" as dyn;

        // 1. R_X86_64_64: S + A
        uint64 sym_addr = 0x00400000 as uint64;
        int64 addend = 16 as int64;
        uint64 v_64 = dyn.dynlink_calc_reloc(dyn.R_X86_64_64, 0 as uint64, sym_addr, addend, 0 as uint64);
        if (v_64 != (0x00400010 as uint64)) return 1;

        // 2. R_X86_64_PC32: S + A - P
        // Symbol is at 0x00401000, patch site P is at 0x00400500, addend = -4
        // Diff = 0x00401000 - 4 - 0x00400500 = 0x00000AFC
        uint64 patch_addr = 0x00400500 as uint64;
        uint64 v_pc32 = dyn.dynlink_calc_reloc(dyn.R_X86_64_PC32, 0 as uint64, 0x00401000 as uint64, -4 as int64, patch_addr);
        if (v_pc32 != (0x00000AFC as uint64)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
