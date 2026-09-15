import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestStdFormat(unittest.TestCase):
    def run_kale_jit(self, code: str) -> int:
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

    def test_format_bool_and_int(self):
        code = """
        import "packages/std/text/format.kl" as fmt;
        extern int strcmp(string s1, string s2);

        string t_str = fmt.format_bool(true);
        string f_str = fmt.format_bool(false);
        if (strcmp(t_str, "true") != 0 || strcmp(f_str, "false") != 0) {
            return 1;
        }

        string i0 = fmt.format_int(0);
        string i42 = fmt.format_int(42);
        string ineg = fmt.format_int(-99);
        if (strcmp(i0, "0") != 0 || strcmp(i42, "42") != 0 || strcmp(ineg, "-99") != 0) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_format_hex(self):
        code = """
        import "packages/std/text/format.kl" as fmt;
        extern int strcmp(string s1, string s2);

        string h0 = fmt.format_hex(0);
        string h255 = fmt.format_hex(255);
        string h42 = fmt.format_hex(42);
        string hneg1 = fmt.format_hex(-1);
        string hneg42 = fmt.format_hex(-42);
        string hneg255 = fmt.format_hex(-255);

        if (strcmp(h0, "0x0") != 0) { return 1; }
        if (strcmp(h255, "0xFF") != 0) { return 2; }
        if (strcmp(h42, "0x2A") != 0) { return 3; }
        if (strcmp(hneg1, "-0x1") != 0) { return 4; }
        if (strcmp(hneg42, "-0x2A") != 0) { return 5; }
        if (strcmp(hneg255, "-0xFF") != 0) { return 6; }

        return 77;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 77)

    def test_pad_left_and_pad_right(self):
        code = """
        import "packages/std/text/format.kl" as fmt;
        extern int strcmp(string s1, string s2);

        string padded_l = fmt.pad_left("42", 5, (char)48); // "00042"
        string padded_r = fmt.pad_right("hi", 4, (char)32); // "hi  "
        string rep = fmt.repeat_char((char)61, 3); // "==="

        if (strcmp(padded_l, "00042") != 0) { return 1; }
        if (strcmp(padded_r, "hi  ") != 0) { return 2; }
        if (strcmp(rep, "===") != 0) { return 3; }

        return 99;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

if __name__ == "__main__":
    unittest.main()
