import unittest
import llvmlite.binding as llvm
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter

class TestLLVMEmitter(unittest.TestCase):
    def test_emit_basic_arithmetic_llvm_ir(self):
        text = SourceText("""
        int a = 10;
        int b = 25;
        int c = a + b;
        print("Result:", c);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        ir_text = str(mod)

        self.assertIn("define i32 @\"main\"()", ir_text)
        self.assertIn("add i64", ir_text)
        self.assertIn("call i32 (ptr, ...) @\"printf\"", ir_text)

        # Verify with LLVM parser
        llvm_mod = llvm.parse_assembly(ir_text)
        llvm_mod.verify()

    def test_emit_control_flow_llvm_ir(self):
        text = SourceText("""
        int x = 10;
        if (x > 5) {
            print("Greater");
        } else {
            print("Smaller");
        }
        while (x > 0) {
            x--;
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
        ir_text = str(mod)

        self.assertIn("br i1", ir_text)
        self.assertIn("if.then", ir_text)
        self.assertIn("if.else", ir_text)
        self.assertIn("while.cond", ir_text)
        self.assertIn("while.body", ir_text)

        llvm_mod = llvm.parse_assembly(ir_text)
        llvm_mod.verify()

if __name__ == "__main__":
    unittest.main()
