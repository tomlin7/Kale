import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestStructZeroInit(unittest.TestCase):
    def run_kale_jit(self, code: str):
        st = SourceText(code)
        diag = DiagnosticBag()
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)
        binder = Binder(diag)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)
        emitter = LLVMEmitter()
        llvm_mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        return jit.run_ir(str(llvm_mod))

    def test_struct_zero_init(self):
        code = """
        struct Rect {
            int left;
            int top;
            int right;
            int bottom;
        }

        Rect r;
        // All fields should default to 0
        return r.left + r.top + r.right + r.bottom;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 0)

if __name__ == "__main__":
    unittest.main()
