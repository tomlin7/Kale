import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.binding.types import TypeInt32, lookup_type

class TestInt32(unittest.TestCase):
    def test_int32_lookup(self):
        self.assertEqual(lookup_type("int32"), TypeInt32)
        self.assertEqual(lookup_type("i32"), TypeInt32)

    def test_int32_arithmetic_and_struct(self):
        text = SourceText("""
        struct Point32 {
            int32 x;
            int32 y;
        };

        Point32 p;
        p.x = 10;
        p.y = 25;
        int sum = (int)(p.x + p.y);
        print(sum);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)
