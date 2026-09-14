import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
import os

class TestUIGeom(unittest.TestCase):
    def test_rect_contains_and_inset(self):
        code = """
        import "libs/ui_native/geom.kl" as geom;

        geom.Rect r;
        r.init(10, 10, 100, 80);

        bool c1 = r.contains(50, 50); // true
        bool c2 = r.contains(5, 5);   // false
        bool c3 = r.contains(10, 10); // true
        bool c4 = r.contains(110, 90);// false

        r.inset(5, 5); // x=15, y=15, w=90, h=70
        bool c5 = r.contains(12, 12); // false
        bool c6 = r.contains(20, 20); // true

        if (c1 && !c2 && c3 && !c4 && !c5 && c6) {
            return 1;
        }
        return 0;
        """
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
        mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        res = jit.run_ir(str(mod))
        self.assertEqual(res, 1)

    def test_color_to_colorref(self):
        code = """
        import "libs/ui_native/geom.kl" as geom;

        geom.Color c;
        c.init(255, 128, 64, 255); // R=255, G=128, B=64
        int cref = c.to_colorref();

        // COLORREF: R | (G << 8) | (B << 16)
        // 255 | (128 << 8) | (64 << 16) = 255 | 32768 | 4194304 = 4227327
        return cref;
        """
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
        mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        res = jit.run_ir(str(mod))
        self.assertEqual(res, 4227327)

if __name__ == "__main__":
    unittest.main()
