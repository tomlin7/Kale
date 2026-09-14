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

    def test_editor_buffer_compaction_and_resize(self):
        code = """
        import "apps/editor/buffer_manager.kl" as bm;
        import "apps/editor/terminal_split.kl" as ts;

        bm.BufferManager* mgr = bm.bufman_new();
        bm.bufman_open(mgr, "1.kl", "1.kl", "1");
        bm.bufman_open(mgr, "2.kl", "2.kl", "2");
        bm.bufman_open(mgr, "3.kl", "3.kl", "3");
        bm.bufman_open(mgr, "4.kl", "4.kl", "4");
        bm.bufman_open(mgr, "5.kl", "5.kl", "5");

        if (mgr->count != 5) {
            return 1;
        }

        bm.bufman_close(mgr, 2);
        if (mgr->count != 4) {
            return 2;
        }

        // Test split resize
        ts.TerminalSplit* term = ts.split_new(80, 24, "term");
        ts.split_set_percent(term, 45);
        if (term->split_percent != 45) {
            return 3;
        }
        ts.split_resize(term, 100, 30);
        if (term->cols != 100 || term->rows != 30) {
            return 4;
        }

        ts.split_free(term);
        bm.bufman_free(mgr);
        return 88;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 88)

    def test_editor_terminal_executor_commands(self):
        code = """
        import "apps/editor/terminal_split.kl" as ts;
        import "libs/term/grid.kl" as grid;

        ts.TerminalSplit* term = ts.split_new(80, 24, "bash");
        
        // Initial state
        if (ts.split_commands_count(term) != 0) {
            return 1;
        }

        // Send input
        ts.split_send_input(term, "echo kale\\n");
        grid.Cell* c = ts.split_cell_at(term, 0, 0);
        if (c->ch != 101) { // 'e' == 101
            return 2;
        }

        // Run clear
        ts.split_clear(term);

        // Run command
        int ret = ts.split_run_command(term, "echo HelloFromKale");
        if (ret != 0) {
            return 3;
        }
        if (ts.split_commands_count(term) != 1) {
            return 4;
        }

        ts.split_free(term);
        return 100;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 100)

if __name__ == "__main__":
    unittest.main()
