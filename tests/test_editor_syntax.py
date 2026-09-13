import unittest
import os
import ctypes
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestSyntax(unittest.TestCase):
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

    def test_syntax_keyword_classification(self):
        code = """
        import "packages/editor/syntax.kl" as syn;

        if (!syn.is_kale_keyword("fn")) {
            return 1;
        }
        if (!syn.is_kale_keyword("struct")) {
            return 2;
        }
        if (!syn.is_kale_keyword("return")) {
            return 3;
        }
        if (syn.is_kale_keyword("my_variable")) {
            return 4;
        }
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_syntax_highlighter_spans(self):
        code = """
        import "packages/editor/syntax.kl" as syn;

        syn.LineHighlighter hl;
        hl.init();

        hl.add_span(0, 2, 1); // "fn"
        hl.add_span(3, 4, 0); // "main"
        hl.add_span(7, 2, 5); // "()"

        if (hl.get_count() != 3) {
            return 1;
        }

        syn.TokenSpan s0 = hl.get_span(0);
        if (s0.start_col != 0 || s0.length != 2 || s0.token_type != 1) {
            return 2;
        }

        hl.destroy();
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_syntax_highlight_line_lexer(self):
        code = """
        import "packages/editor/syntax.kl" as syn;

        syn.LineHighlighter hl;
        hl.init();

        hl.highlight_line("fn main() { int x = 42; } // done");
        int total = hl.get_count();
        if (total < 7) {
            return 1;
        }

        syn.TokenSpan s0 = hl.get_span(0);
        if (s0.token_type != 1 || s0.length != 2) {
            return 2;
        }

        syn.TokenSpan s1 = hl.get_span(1);
        if (s1.token_type != 0 || s1.length != 4) {
            return 3;
        }

        hl.destroy();
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
