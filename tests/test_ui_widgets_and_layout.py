import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestUIWidgetsAndLayout(unittest.TestCase):
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

    def test_ui_layout_column_and_row(self):
        code = """
        import "libs/ui/layout.kl" as lay;

        lay.UILayout col = lay.layout_begin_column(10.0, 20.0, 200.0, 400.0, 8.0, 4.0);
        // Start pos should be x=14, y=24
        lay.Rect r1 = lay.layout_next_item(&col, 180.0, 30.0);
        lay.Rect r2 = lay.layout_next_item(&col, 180.0, 30.0);

        // r1: y = 24.0, next y will be 24 + 30 + 8 = 62.0
        if (r1.x < 13.9 || r1.x > 14.1) {
            return 1;
        }
        if (r1.y < 23.9 || r1.y > 24.1) {
            return 2;
        }
        if (r2.y < 61.9 || r2.y > 62.1) {
            return 3;
        }

        lay.UILayout row = lay.layout_begin_row(0.0, 0.0, 500.0, 100.0, 10.0, 5.0);
        lay.Rect item1 = lay.layout_next_item(&row, 50.0, 30.0);
        lay.Rect item2 = lay.layout_next_item(&row, 70.0, 30.0);

        // item1: x = 5.0, next x will be 5 + 50 + 10 = 65.0
        if (item1.x < 4.9 || item1.x > 5.1) {
            return 4;
        }
        if (item2.x < 64.9 || item2.x > 65.1) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
