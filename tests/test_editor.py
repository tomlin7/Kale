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

class TestEditor(unittest.TestCase):
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

    def test_editor_buffer_and_cursor(self):
        code = """
        import "packages/editor/editor.kl" as ed;

        ed.Editor editor;
        editor.init(800, 600);

        editor.load_text("fn main() {\\n    return 0;\\n}\\n");
        if (editor.buffer.line_count() < 3) {
            return 1;
        }

        // Insert at cursor (row 0, col 0)
        editor.insert_char_at_cursor("// Hello\\n");
        if (editor.buffer.line_count() < 4) {
            return 2;
        }

        editor.destroy();
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_editor_window_and_rendering(self):
        code = """
        import "packages/editor/editor.kl" as ed;

        ed.Editor editor;
        editor.init(640, 480);
        editor.load_text("line 1\\nline 2\\nline 3");

        bool ok = editor.open_window("Kale Editor Test");
        if (!ok) {
            return 1;
        }

        editor.render();
        bool polled = editor.window.poll_events();
        if (!polled) {
            return 2;
        }

        editor.destroy();
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
