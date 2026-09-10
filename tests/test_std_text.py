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

class TestStdText(unittest.TestCase):
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

    def test_piece_table_basic(self):
        code = """
        import "packages/std/text/piece_table.kl" as pt;
        extern int strlen(string s);

        pt.PieceTable buf;
        buf.init("Hello World");
        
        int initial_len = buf.total_length();
        
        // Insert " Brave" at offset 5 ("Hello Brave World")
        buf.insert(5, " Brave");
        int after_insert_len = buf.total_length();

        // Delete " Brave" (offset 5, length 6) -> back to "Hello World"
        buf.delete(5, 6);
        int after_delete_len = buf.total_length();

        string content = buf.get_text();
        int content_len = strlen(content);
        buf.destroy();

        if (initial_len != 11) {
            return 1;
        }
        if (after_insert_len != 17) {
            return 2;
        }
        if (after_delete_len != 11) {
            return 3;
        }
        if (content_len != 11) {
            return 4;
        }
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_piece_table_multiline(self):
        code = r"""
        import "packages/std/text/piece_table.kl" as pt;
        extern int strlen(string s);

        pt.PieceTable buf;
        buf.init("fn main() {\n    return 0;\n}");
        
        // Insert line in middle: offset 12 is right after first newline
        buf.insert(12, "    int x = 42;\n");
        string code_str = buf.get_text();
        int final_len = strlen(code_str);
        buf.destroy();

        // Original was 27 bytes, added 16 bytes = 43 bytes
        return final_len;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 43)

    def test_piece_table_lines(self):
        code = r"""
        import "packages/std/text/piece_table.kl" as pt;
        extern int strlen(string s);

        pt.PieceTable buf;
        buf.init("line 0\nline 1\nline 2");

        int count = buf.line_count();
        string l0 = buf.get_line(0);
        string l1 = buf.get_line(1);
        string l2 = buf.get_line(2);

        int len0 = strlen(l0);
        int len1 = strlen(l1);
        int len2 = strlen(l2);

        buf.destroy();

        if (count != 3) {
            return 1;
        }
        if (len0 != 6 || len1 != 6 || len2 != 6) {
            return 2;
        }
        return 77;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 77)

if __name__ == "__main__":
    unittest.main()
