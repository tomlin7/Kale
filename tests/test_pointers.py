import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestPointers(unittest.TestCase):
    def test_address_of_and_prefix_deref_jit(self):
        text = SourceText('''
        int x = 42;
        int* p = &x;
        *p = 100;
        print(x, *p);
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

    def test_postfix_caret_deref_jit(self):
        text = SourceText('''
        int val = 50;
        int* ptr = &val;
        ptr^ = 75;
        print(ptr^);
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

    def test_pointer_to_struct_arrow_jit(self):
        text = SourceText('''
        struct Point {
            int x;
            int y;
        };

        Point pt;
        Point* p = &pt;
        p->x = 123;
        p->y = 456;
        print(p->x, p->y, pt.x, pt.y);
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

    def test_pointer_pass_by_reference_function_jit(self):
        text = SourceText('''
        void increment(int* num) {
            *num += 10;
        }

        int a = 15;
        increment(&a);
        print(a);
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

    def test_dynamic_alloc_and_free_jit(self):
        text = SourceText('''
        int* buffer = alloc(int, 5);
        buffer[0] = 10;
        buffer[1] = 20;
        buffer[2] = 30;
        int sum = buffer[0] + buffer[1] + buffer[2];
        print(sum);
        free(buffer);
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

    def test_dynamic_struct_alloc_arrow_jit(self):
        text = SourceText('''
        struct Node {
            int value;
            int priority;
        };

        Node* n = alloc(Node);
        n->value = 999;
        n->priority = 1;
        print(n->value, n->priority);
        free(n);
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

    def test_dereference_non_pointer_diagnostic(self):
        text = SourceText('''
        int x = 10;
        int y = *x;
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)
        self.assertTrue(diag.has_errors)
        errors = [d.message for d in diag]
        self.assertTrue(any("Cannot dereference non-pointer" in m for m in errors))

    def test_arrow_on_non_struct_pointer_diagnostic(self):
        text = SourceText('''
        int x = 10;
        int* p = &x;
        int y = p->foo;
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)
        self.assertTrue(diag.has_errors)
        errors = [d.message for d in diag]
        self.assertTrue(any("Cannot use '->' operator on non-struct pointer" in m for m in errors))

    def test_c_emitter_pointers(self):
        text = SourceText('''
        int x = 42;
        int* p = &x;
        *p = 100;
        print(*p);
        free(p);
        ''')
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)

        c_emitter = CEmitter()
        c_code = c_emitter.emit(program)
        self.assertIn("long long* p = (&(x));", c_code)
        self.assertIn("(*(p)) = 100;", c_code)
        self.assertIn("free((void*)(p));", c_code)

if __name__ == '__main__':
    unittest.main()
