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
from kale.codegen.c_emitter import CEmitter

class TestWin32Bindings(unittest.TestCase):
    def setUp(self):
        # Ensure user32 is loaded into process address space
        ctypes.windll.user32.GetSystemMetrics(0)

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

    def test_win32_system_metrics(self):
        code = """
        import "packages/bindings/win32/user32.kl" as u32;

        int w = u32.sm_cx_screen();
        int h = u32.sm_cy_screen();

        if (w <= 0 || h <= 0) {
            return 1;
        }
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_win32_window_abstraction(self):
        code = """
        import "packages/bindings/win32/window.kl" as win;

        win.Window w;
        w.init(800, 600);

        if (w.width != 800 || w.height != 600 || !w.is_open) {
            return 1;
        }

        w.close();
        if (w.is_open) {
            return 2;
        }
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
