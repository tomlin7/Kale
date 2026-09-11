import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestFunctionPointers(unittest.TestCase):
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

    def test_basic_function_pointer(self):
        code = """
        int add(int a, int b) {
            return a + b;
        }

        int sub(int a, int b) {
            return a - b;
        }

        fn(int, int): int op = add;
        int r1 = op(10, 20);

        op = sub;
        int r2 = op(50, 15);

        return r1 + r2; // 30 + 35 = 65
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 65)

    def test_higher_order_function_callback(self):
        code = """
        int square(int x) {
            return x * x;
        }

        int apply(fn(int): int callback, int val) {
            return callback(val);
        }

        return apply(square, 9); // 81
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 81)

    def test_struct_with_function_pointer(self):
        code = """
        int double_val(int x) {
            return x * 2;
        }

        struct Button {
            int id;
            fn(int): int on_click;
        }

        Button btn;
        btn.id = 1;
        btn.on_click = double_val;

        fn(int): int cb = btn.on_click;
        return cb(21); // 42
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
