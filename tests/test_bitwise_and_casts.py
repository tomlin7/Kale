import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestBitwiseAndCasts(unittest.TestCase):
    def _run_jit(self, src: str) -> int:
        text = SourceText(src)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, [d.message for d in diag])

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)
        jit = LLVMJIT()
        return jit.run_ir(str(mod))

    def test_bitwise_operations(self):
        src = '''
        int a = 10 & 12;
        int b = 10 | 5;
        int c = 10 ^ 12;
        int d = 1 << 4;
        int e = 32 >> 2;
        int f = (~0) & 255;
        int res = a + b + c + d + e + f;
        return res;
        '''
        self.assertEqual(self._run_jit(src), 308)

    def test_bitwise_operator_precedence(self):
        src = '''
        int x = 1 << 2 + 1;
        int z = 12 & 4 + 4;
        return x + z;
        '''
        self.assertEqual(self._run_jit(src), 16)

    def test_bitwise_compound_assignments(self):
        src = '''
        int x = 1;
        x <<= 3;
        x |= 2;
        x &= 14;
        x ^= 3;
        x >>= 1;
        return x;
        '''
        self.assertEqual(self._run_jit(src), 4)

    def test_explicit_c_style_numeric_casts(self):
        src = '''
        double pi = 3.14159;
        int int_pi = (int)pi;
        double back_to_dbl = (double)int_pi;
        char ch = (char)65;
        int ascii_code = (int)ch;
        return int_pi + ascii_code;
        '''
        self.assertEqual(self._run_jit(src), 68)

    def test_explicit_as_keyword_casts(self):
        src = '''
        double val = 42.99;
        int truncated = val as int;
        char letter = 66 as char;
        int code = letter as int;
        return truncated + code;
        '''
        self.assertEqual(self._run_jit(src), 108)

    def test_pointer_to_pointer_and_pointer_to_int_casts(self):
        src = '''
        int* p = alloc(int, 2);
        p[0] = 42;
        p[1] = 99;

        int addr = (int)p;
        int* p2 = (int*)addr;

        char* byte_ptr = p as char*;
        byte_ptr[0] = (char)7;

        int res = p2[0];
        free(p);
        return res;
        '''
        self.assertEqual(self._run_jit(src), 7)

    def test_c_emitter_with_casts_and_bitwise(self):
        src = '''
        int a = 255;
        int b = a << 2;
        int c = (int)3.5;
        int d = b as int;
        '''
        text = SourceText(src)
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        emitter = CEmitter()
        c_code = emitter.emit(program)
        self.assertIn("3.5", c_code)
        self.assertIn("<<", c_code)

if __name__ == '__main__':
    unittest.main()
