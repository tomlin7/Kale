import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestStructs(unittest.TestCase):
    def test_struct_declaration_and_field_access_jit(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        Point p;
        p.x = 10;
        p.y = 25;
        print(p.x, p.y);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)
        self.assertEqual(len(program.structs), 1)

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_struct_field_mutation_and_arithmetic_jit(self):
        text = SourceText('''
        struct Vector3 {
            double x;
            double y;
            double z;
        };

        Vector3 v;
        v.x = 1.5;
        v.y = 2.5;
        v.z = 3.0;
        v.x += 10.0;
        double sum = v.x + v.y + v.z;
        print(sum);
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

    def test_nested_struct_jit(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        struct Rectangle {
            Point origin;
            int width;
            int height;
        };

        Rectangle r;
        r.origin.x = 100;
        r.origin.y = 200;
        r.width = 50;
        r.height = 25;
        r.origin.x += 25;
        print(r.origin.x, r.origin.y, r.width * r.height);
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

    def test_invalid_field_access_diagnostic(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        Point p;
        p.z = 100;
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)
        self.assertTrue(diag.has_errors)
        errors = [d.message for d in diag]
        self.assertTrue(any("has no field named 'z'" in m for m in errors))

    def test_access_member_of_non_struct_diagnostic(self):
        text = SourceText('''
        int x = 42;
        int y = x.foo;
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)
        self.assertTrue(diag.has_errors)
        errors = [d.message for d in diag]
        self.assertTrue(any("Cannot access member of non-struct type" in m for m in errors))

    def test_c_emitter_struct(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        Point p;
        p.x = 42;
        p.y = 84;
        print(p.x);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        c_emitter = CEmitter()
        c_code = c_emitter.emit(program)
        self.assertIn("struct Point {", c_code)
        self.assertIn("long long x;", c_code)
        self.assertIn("p.x = 42;", c_code)

if __name__ == '__main__':
    unittest.main()
