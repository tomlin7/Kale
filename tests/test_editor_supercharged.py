import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestEditorSupercharged(unittest.TestCase):
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

    def test_editor_buffer_and_terminal_split(self):
        code = """
        import "apps/editor/buffer_manager.kl" as bm;
        import "apps/editor/terminal_split.kl" as ts;
        import "apps/editor/layout.kl" as layout;
        import "libs/term/grid.kl" as grid;

        bm.BufferManager* mgr = bm.bufman_new();
        bm.bufman_open(mgr, "a.kl", "a.kl", "fn a() {}\\n");
        bm.bufman_open(mgr, "b.kl", "b.kl", "fn b() {}\\n");

        if (mgr->count != 2) {
            return 1;
        }

        ts.TerminalSplit* term = ts.split_new(80, 24, "term");
        ts.split_write(term, "hello\\n");
        grid.Cell* c = ts.split_cell_at(term, 0, 0);
        if (c->ch != 104) { // 'h' == 104
            return 2;
        }

        layout.IdeLayout lay = layout.calculate_layout(800, 600, term);
        if (lay.terminal_pane.h <= 0) {
            return 3;
        }

        ts.split_free(term);
        bm.bufman_free(mgr);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
