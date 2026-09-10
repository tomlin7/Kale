import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter

class TestGenerics(unittest.TestCase):
    def run_kale_jit(self, code: str):
        st = SourceText(code)
        diag = DiagnosticBag()
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parser errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Binder errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        llvm_mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        return jit.run_ir(str(llvm_mod))

    def run_kale_c(self, code: str) -> str:
        st = SourceText(code)
        diag = DiagnosticBag()
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parser errors: {[d.message for d in diag]}")

        binder = Binder(diag)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Binder errors: {[d.message for d in diag]}")

        emitter = CEmitter()
        return emitter.emit(bound)

    def test_generic_struct_single_param(self):
        code = """
        struct Box<T> {
            T value;
        }

        Box<int> b;
        b.value = 42;
        print(b.value);
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)

    def test_generic_struct_multiple_params(self):
        code = """
        struct Pair<A, B> {
            A first;
            B second;
        }

        Pair<int, double> p;
        p.first = 100;
        p.second = 3.14;
        print(p.first, p.second);
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)

    def test_generic_struct_with_methods(self):
        code = """
        struct Container<T> {
            T item;
        }

        fn void Container.set(T val) {
            this->item = val;
        }

        fn T Container.get() {
            return this->item;
        }

        Container<int> c;
        c.set(999);
        print(c.get());
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)

    def test_generic_function_identity(self):
        code = """
        fn T identity<T>(T val) {
            return val;
        }

        int a = identity(123);
        double b = identity(4.56);
        print(a, b);
        """
        ret = self.run_kale_jit(code)
        self.assertEqual(ret, 0)

    def test_generic_c_emission(self):
        code = """
        struct Pair<A, B> {
            A first;
            B second;
        }

        Pair<int, string> p;
        p.first = 7;
        p.second = "hello";
        print(p.first, p.second);
        """
        c_code = self.run_kale_c(code)
        self.assertIn("struct Pair_int_string", c_code)
        self.assertIn("long long first;", c_code)
        self.assertIn("const char* second;", c_code)
