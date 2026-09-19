import unittest
import os
import ctypes
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestEditorCommandBar(unittest.TestCase):
    def setUp(self):
        ctypes.windll.user32.GetSystemMetrics(0)
        ctypes.windll.gdi32.GetStockObject(0)

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

    def test_editor_undo_redo(self):
        code = """
        import "editor/app_state.kl" as st;

        st.EditorState state;
        state.init("hello", "test.kl");

        // Insert ' world'
        state.cursor_col = 5;
        state.insert_char(" world");
        if (state.cursor_col != 11) {
            return 1;
        }

        // Test Undo
        state.undo();
        if (state.cursor_col != 5) {
            return 2;
        }

        // Test Redo
        state.redo();
        if (state.cursor_col != 11) {
            return 3;
        }

        state.destroy();
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_command_bar_navigation(self):
        code = """
        import "editor/command_bar.kl" as cb;

        cb.CommandBar bar;
        bar.init();

        if (bar.is_visible) {
            return 1;
        }

        bar.toggle();
        if (!bar.is_visible) {
            return 2;
        }

        // Default selection: index 0
        if (bar.selected_index != 0) {
            return 3;
        }

        bar.select_next();
        if (bar.selected_index != 1) {
            return 4;
        }

        bar.select_prev();
        if (bar.selected_index != 0) {
            return 5;
        }

        // Wrap around backward
        bar.select_prev();
        if (bar.selected_index != bar.items_count - 1) {
            return 6;
        }

        int id = bar.get_selected_id();
        if (id != 6) {
            return 7;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
