import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestOperatorOverloading(unittest.TestCase):
    def test_vector_addition_method_jit(self):
        text = SourceText('''
        struct Vec2 {
            int x;
            int y;
        };

        fn Vec2 Vec2.operator+(Vec2* other) {
            Vec2 res;
            res.x = this->x + other->x;
            res.y = this->y + other->y;
            return res;
        }

        Vec2 v1;
        v1.x = 10;
        v1.y = 20;

        Vec2 v2;
        v2.x = 30;
        v2.y = 40;

        Vec2 v3 = v1 + v2;
        print(v3.x, v3.y);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_vector_standalone_operator_jit(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        fn Point operator+(Point* a, Point* b) {
            Point p;
            p.x = a->x + b->x;
            p.y = a->y + b->y;
            return p;
        }

        Point p1;
        p1.x = 5;
        p1.y = 15;

        Point p2;
        p2.x = 25;
        p2.y = 35;

        Point p3 = p1 + p2;
        print(p3.x, p3.y);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_scalar_multiplication_jit(self):
        text = SourceText('''
        struct Vec2 {
            int x;
            int y;
        };

        fn Vec2 Vec2.operator*(int scale) {
            Vec2 res;
            res.x = this->x * scale;
            res.y = this->y * scale;
            return res;
        }

        Vec2 v;
        v.x = 3;
        v.y = 7;

        Vec2 v2 = v * 5;
        print(v2.x, v2.y);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_equality_operator_jit(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        fn bool Point.operator==(Point* other) {
            return this->x == other->x && this->y == other->y;
        }

        fn bool Point.operator!=(Point* other) {
            return !(this == other);
        }

        Point a;
        a.x = 10;
        a.y = 20;

        Point b;
        b.x = 10;
        b.y = 20;

        Point c;
        c.x = 10;
        c.y = 30;

        bool eq1 = (a == b);
        bool eq2 = (a == c);
        bool ne1 = (a != c);
        print(eq1, eq2, ne1);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_unary_operator_jit(self):
        text = SourceText('''
        struct Vec2 {
            int x;
            int y;
        };

        fn Vec2 Vec2.operator-() {
            Vec2 res;
            res.x = -this->x;
            res.y = -this->y;
            return res;
        }

        Vec2 v;
        v.x = 42;
        v.y = -84;

        Vec2 neg_v = -v;
        print(neg_v.x, neg_v.y);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_custom_indexer_operator_jit(self):
        text = SourceText('''
        struct IntPair {
            int first;
            int second;
        };

        fn int IntPair.operator[](int idx) {
            if (idx == 0) {
                return this->first;
            }
            return this->second;
        }

        IntPair p;
        p.first = 100;
        p.second = 200;

        int a = p[0];
        int b = p[1];
        print(a, b);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parse errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Bind errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        mod = emitter.emit_module(program)

        jit = LLVMJIT()
        ret = jit.run_ir(str(mod))
        self.assertEqual(ret, 0)

    def test_c_emitter_operator_overload(self):
        text = SourceText('''
        struct Vec2 {
            int x;
            int y;
        };

        fn Vec2 Vec2.operator+(Vec2* other) {
            Vec2 res;
            res.x = this->x + other->x;
            res.y = this->y + other->y;
            return res;
        }

        Vec2 a;
        Vec2 b;
        Vec2 c = a + b;
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        c_emitter = CEmitter()
        c_code = c_emitter.emit(program)
        self.assertIn("kale_Vec2_op_add", c_code)
        self.assertIn("&(a)", c_code)
        self.assertIn("&(b)", c_code)

if __name__ == "__main__":
    unittest.main()
