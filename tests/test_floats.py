import unittest
from kale.syntax.lexer import Lexer
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.types import TypeFloat, TypeDouble, TypeInt, TypeInt32
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.diagnostics.source_text import SourceText

class TestFloats(unittest.TestCase):
    def _bind(self, code: str):
        diag = DiagnosticBag()
        src = SourceText(code)
        parser = Parser(src, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        prog = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, [d.message for d in diag])
        return prog

    def _eval(self, code: str) -> int:
        prog = self._bind(code)
        emitter = LLVMEmitter()
        mod = emitter.emit_module(prog)
        jit = LLVMJIT()
        return jit.run_ir(str(mod))

    def test_float_primitives_binding(self):
        code = """
        float a = 3.14f;
        float32 b = 1.5f;
        f32 c = 2.0f;
        double d = 2.71828;
        float64 e = 10.5;
        f64 f = 20.0;
        """
        prog = self._bind(code)
        vars = {v.name: v.type for stmt in prog.statements if hasattr(stmt, 'variable') for v in [stmt.variable]}
        self.assertEqual(vars["a"], TypeFloat)
        self.assertEqual(vars["b"], TypeFloat)
        self.assertEqual(vars["c"], TypeFloat)
        self.assertEqual(vars["d"], TypeDouble)
        self.assertEqual(vars["e"], TypeDouble)
        self.assertEqual(vars["f"], TypeDouble)

    def test_float_arithmetic_and_return(self):
        code = """
        float x = 10.5f;
        float y = 4.5f;
        float sum = x + y; // 15.0f
        float diff = x - y; // 6.0f
        float prod = diff * 2.0f; // 12.0f
        int res = (int)prod; // 12
        return res;
        """
        self.assertEqual(self._eval(code), 12)

    def test_float_double_coercion(self):
        code = """
        float a = 2.5f;
        double b = 3.5;
        double sum = a + b; // 6.0
        return (int)sum;
        """
        self.assertEqual(self._eval(code), 6)

    def test_float_comparisons(self):
        code = """
        float x = 5.5f;
        float y = 10.2f;
        if (x < y && y > 10.0f && x == 5.5f) {
            return 42;
        }
        return 0;
        """
        self.assertEqual(self._eval(code), 42)

    def test_float_compound_assignment(self):
        code = """
        float x = 5.0f;
        x += 3.5f; // 8.5
        x *= 2.0f; // 17.0
        return (int)x;
        """
        self.assertEqual(self._eval(code), 17)

    def test_float_function_calls(self):
        code = """
        fn float add_floats(float a, float b) {
            return a + b;
        }

        fn double mul_doubles(double a, double b) {
            return a * b;
        }

        float res1 = add_floats(1.25f, 2.75f); // 4.0f
        double res2 = mul_doubles(3.0, 5.0); // 15.0
        return (int)(res1 + (float)res2); // 19
        """
        self.assertEqual(self._eval(code), 19)

if __name__ == "__main__":
    unittest.main()
