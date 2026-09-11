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

class TestStdStringBuilder(unittest.TestCase):
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

    def test_string_builder_basic(self):
        code = """
        import "packages/std/text/string_builder.kl" as sb;
        extern int strlen(string s);

        sb.StringBuilder b;
        b.init(8);

        b.append("Hello");
        b.append_char((char)32); // ' '
        b.append("Kale");
        b.append_char((char)33); // '!'

        string s = b.to_string();
        int len = strlen(s);
        b.destroy();

        // "Hello Kale!" is 11 chars
        return len;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 11)

    def test_string_builder_append_int_and_line(self):
        code = r"""
        import "packages/std/text/string_builder.kl" as sb;
        extern int strlen(string s);

        sb.StringBuilder b;
        b.init(16);

        b.append("Answer: ");
        b.append_int(42);
        b.append_char((char)10); // '\n'
        b.append("Negative: ");
        b.append_int(-100);

        string s = b.to_string();
        int len = strlen(s);
        b.destroy();

        // "Answer: 42\nNegative: -100" -> 11 + 14 = 25 chars
        return len;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 25)

if __name__ == "__main__":
    unittest.main()
