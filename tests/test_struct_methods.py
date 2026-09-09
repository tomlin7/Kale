import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestStructMethods(unittest.TestCase):
    def test_struct_method_basic_jit(self):
        text = SourceText('''
        struct Rectangle {
            int width;
            int height;
        };

        fn int Rectangle.area() {
            return this->width * this->height;
        }

        Rectangle r;
        r.width = 5;
        r.height = 10;
        int a = r.area();
        print(a);
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

    def test_struct_method_mutation_jit(self):
        text = SourceText('''
        struct Counter {
            int count;
        };

        fn void Counter.increment(int delta) {
            this->count += delta;
        }

        fn int Counter.get() {
            return this->count;
        }

        Counter c;
        c.count = 0;
        c.increment(5);
        c.increment(10);
        print(c.get());
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

    def test_struct_pointer_method_call_jit(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        fn void Point.set(int new_x, int new_y) {
            this->x = new_x;
            this->y = new_y;
        }

        fn int Point.sum() {
            return this->x + this->y;
        }

        Point* p = alloc(Point);
        p->set(20, 30);
        int total = p->sum();
        print(total);
        free(p);
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

    def test_struct_method_c_emitter(self):
        text = SourceText('''
        struct Vector {
            double x;
            double y;
        };

        fn double Vector.dot(double other_x, double other_y) {
            return (this->x * other_x) + (this->y * other_y);
        }

        Vector v;
        v.x = 2.0;
        v.y = 3.0;
        double d = v.dot(4.0, 5.0);
        print(d);
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
        self.assertIn("struct Vector", c_code)
        self.assertIn("kale_Vector_dot", c_code)
        self.assertIn("&(v)", c_code)

if __name__ == "__main__":
    unittest.main()
