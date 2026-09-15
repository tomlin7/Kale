import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestStdMem(unittest.TestCase):
    def run_kale_jit(self, code: str) -> int:
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

    def test_arena_basic_alloc(self):
        code = """
        import "packages/std/core/mem.kl" as mem;

        mem.Arena arena;
        arena.init(128);

        char* p1 = arena.alloc_bytes(16);
        if (p1 == (char*)0) { return 1; }
        p1[0] = (char)65; // 'A'
        p1[1] = (char)66; // 'B'
        p1[15] = (char)90; // 'Z'

        char* p2 = arena.alloc_bytes(32);
        if (p2 == (char*)0) { return 2; }
        p2[0] = (char)49; // '1'

        int total = arena.get_total_allocated();
        bool ok = (total == 48 && p1[0] == (char)65 && p1[15] == (char)90 && p2[0] == (char)49);
        arena.destroy();

        if (ok) {
            return 42;
        }
        return total;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_arena_multi_block_growth(self):
        code = """
        import "packages/std/core/mem.kl" as mem;

        mem.Arena arena;
        arena.init(64);

        char* p1 = arena.alloc_bytes(40);
        char* p2 = arena.alloc_bytes(40); // Exceeds first block capacity of 64

        int blk_cnt = arena.get_block_count();
        arena.destroy();

        if (blk_cnt >= 2) {
            return 88;
        }
        return blk_cnt;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 88)

    def test_arena_reset_and_reuse(self):
        code = """
        import "packages/std/core/mem.kl" as mem;

        mem.Arena arena;
        arena.init(128);

        char* p1 = arena.alloc_bytes(64);
        p1[0] = (char)77;

        arena.reset();
        int after_reset = arena.get_total_allocated();
        if (after_reset != 0) {
            arena.destroy();
            return 1;
        }

        char* p2 = arena.alloc_bytes(32);
        p2[0] = (char)88;
        int total = arena.get_total_allocated();
        bool ok = (total == 32 && p2[0] == (char)88);

        arena.destroy();

        if (ok) {
            return 99;
        }
        return 2;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

    def test_arena_multi_block_reset_reuse(self):
        code = """
        import "packages/std/core/mem.kl" as mem;

        mem.Arena arena;
        arena.init(64);

        // First pass: allocate across 2 blocks
        char* a1 = arena.alloc_bytes(40);
        char* a2 = arena.alloc_bytes(40);
        int blks_pass1 = arena.get_block_count();

        // Reset and reallocate same workload
        arena.reset();
        char* b1 = arena.alloc_bytes(40);
        char* b2 = arena.alloc_bytes(40);
        int blks_pass2 = arena.get_block_count();

        arena.destroy();

        // block_count should not increase on pass 2 because existing blocks are reused
        if (blks_pass1 == 2 && blks_pass2 == 2) {
            return 123;
        }
        return blks_pass2;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 123)

if __name__ == "__main__":
    unittest.main()
