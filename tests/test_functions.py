import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestFunctions(unittest.TestCase):
    def test_function_declaration_and_call_jit(self):
        text = SourceText("""
        int add(int a, int b) {
            return a + b;
        }
        int res = add(15, 27);
        print("Sum:", res);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)
        self.assertEqual(len(program.functions), 1)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_recursive_factorial_jit(self):
        text = SourceText("""
        int factorial(int n) {
            if (n <= 1) {
                return 1;
            }
            return n * factorial(n - 1);
        }
        int fact5 = factorial(5);
        print("5! =", fact5);
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

    def test_recursive_fibonacci_jit(self):
        text = SourceText("""
        int fib(int n) {
            if (n <= 0) {
                return 0;
            }
            if (n == 1) {
                return 1;
            }
            return fib(n - 1) + fib(n - 2);
        }
        int f8 = fib(8);
        print("fib(8) =", f8);
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

    def test_mutual_recursion(self):
        text = SourceText("""
        bool isEven(int n) {
            if (n == 0) {
                return true;
            }
            return isOdd(n - 1);
        }
        bool isOdd(int n) {
            if (n == 0) {
                return false;
            }
            return isEven(n - 1);
        }
        bool even4 = isEven(4);
        print("isEven(4):", even4);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)
        self.assertEqual(len(program.functions), 2)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_argument_count_mismatch(self):
        text = SourceText("""
        int add(int a, int b) {
            return a + b;
        }
        int x = add(5);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        self.assertTrue(any("expects 2 arguments, but got 1" in d.message for d in diag))

    def test_argument_type_mismatch(self):
        text = SourceText("""
        int add(int a, int b) {
            return a + b;
        }
        int x = add("hello", 5);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        self.assertTrue(any("Cannot convert type 'string' to 'int'" in d.message for d in diag))

    def test_return_type_mismatch(self):
        text = SourceText("""
        int bad() {
            return "string_not_int";
        }
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        self.assertTrue(any("Cannot convert type 'string' to 'int'" in d.message for d in diag))

    def test_c_emitter_with_functions(self):
        text = SourceText("""
        int multiply(int a, int b) {
            return a * b;
        }
        int result = multiply(6, 7);
        print("Result:", result);
        """)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = CEmitter()
        c_code = emitter.emit(program)
        self.assertIn("long long multiply(long long a, long long b);", c_code)
        self.assertIn("long long multiply(long long a, long long b) {", c_code)
        self.assertIn("multiply(6, 7)", c_code)

if __name__ == "__main__":
    unittest.main()
