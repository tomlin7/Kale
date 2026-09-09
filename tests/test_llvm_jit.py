import unittest
import io
import sys
from contextlib import redirect_stdout
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestLLVMJIT(unittest.TestCase):
    def test_jit_arithmetic_execution(self):
        text = SourceText("""
        int a = 12;
        int b = 30;
        int c = a * b;
        print("Product:", c);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_jit_fibonacci_execution(self):
        text = SourceText("""
        int n = 7;
        int a = 0;
        int b = 1;
        int i = 0;
        while (i < n) {
            print(a);
            int next = a + b;
            a = b;
            b = next;
            i++;
        }
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

if __name__ == "__main__":
    unittest.main()
