import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestArrays(unittest.TestCase):
    def test_array_literal_and_indexing_jit(self):
        text = SourceText('''
        int[] arr = [10, 20, 30, 40];
        int a0 = arr[0];
        int a2 = arr[2];
        print(a0, a2);
        ''')
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

    def test_array_element_mutation_jit(self):
        text = SourceText('''
        int[] arr = [1, 2, 3];
        arr[1] = 99;
        print(arr[1]);
        ''')
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

    def test_array_loop_sum_jit(self):
        text = SourceText('''
        int[] numbers = [10, 20, 30, 40, 50];
        int total = 0;
        for (int i = 0; i < 5; i++) {
            total += numbers[i];
        }
        print(total);
        ''')
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

    def test_array_passed_to_function_jit(self):
        text = SourceText('''
        int sum_array(int[] a, int n) {
            int s = 0;
            for (int i = 0; i < n; i++) {
                s += a[i];
            }
            return s;
        }
        int[] data = [5, 10, 15, 20];
        int res = sum_array(data, 4);
        print(res);
        ''')
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

    def test_indexing_non_array_diagnostic(self):
        text = SourceText('''
        int x = 10;
        int y = x[0];
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)
        self.assertTrue(diag.has_errors)
        errors = [d.message for d in diag]
        self.assertTrue(any("Cannot index a non-array type" in m for m in errors))

    def test_c_emitter_array(self):
        text = SourceText('''
        int[] vals = [1, 2, 3];
        vals[0] = 10;
        print(vals[0]);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        c_emitter = CEmitter()
        c_code = c_emitter.emit(program)
        self.assertIn("long long* vals", c_code)
        self.assertIn("vals[0] = 10;", c_code)

if __name__ == '__main__':
    unittest.main()
