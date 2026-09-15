import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestKaleSelfChecker(unittest.TestCase):
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

    def test_scope_and_symbol_management(self):
        code = """
        import "src/kale_self/checker.kl" as chk;

        chk.Scope* root = chk.scope_new((chk.Scope*)0);
        bool d1 = chk.scope_define(root, "x", chk.SYM_VAR(), chk.TYPE_INT(), "int");
        if (!d1) { return 1; }

        // Duplicate in same scope should fail
        bool d2 = chk.scope_define(root, "x", chk.SYM_VAR(), chk.TYPE_INT(), "int");
        if (d2) { return 2; }

        chk.Symbol* s1 = chk.scope_lookup(root, "x");
        if (s1 == (chk.Symbol*)0 || s1->type_tag != chk.TYPE_INT()) { return 3; }

        // Child scope can shadow parent
        chk.Scope* child = chk.scope_new(root);
        bool d3 = chk.scope_define(child, "x", chk.SYM_VAR(), chk.TYPE_FLOAT(), "float");
        if (!d3) { return 4; }

        chk.Symbol* s2 = chk.scope_lookup(child, "x");
        if (s2 == (chk.Symbol*)0 || s2->type_tag != chk.TYPE_FLOAT()) { return 5; }

        chk.scope_free(child);
        chk.scope_free(root);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_checker_valid_program(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;
        import "src/kale_self/checker.kl" as chk;

        string src = "fn int add(int a, int b) { let c = a + b; return c; }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);
        ast.ASTNode* prog = ps.parser_parse_program(p);

        chk.Checker* c = chk.checker_new();
        int errs = chk.checker_check_program(c, prog);

        ast.ast_free(prog);
        chk.checker_free(c);
        ps.parser_free(p);
        lx.lexer_free(l);

        if (errs == 0) {
            return 100;
        }
        return errs;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 100)

    def test_checker_detects_undeclared_variable(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;
        import "src/kale_self/checker.kl" as chk;

        // 'unknown_var' is never declared
        string src = "fn compute(int a) { return a + unknown_var; }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);
        ast.ASTNode* prog = ps.parser_parse_program(p);

        chk.Checker* c = chk.checker_new();
        int errs = chk.checker_check_program(c, prog);

        ast.ast_free(prog);
        chk.checker_free(c);
        ps.parser_free(p);
        lx.lexer_free(l);

        if (errs > 0) {
            return 88;
        }
        return 0;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 88)

    def test_checker_detects_duplicate_definition(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;
        import "src/kale_self/checker.kl" as chk;

        // duplicate 'val' declared in same block
        string src = "fn test() { let val = 1; let val = 2; return val; }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);
        ast.ASTNode* prog = ps.parser_parse_program(p);

        chk.Checker* c = chk.checker_new();
        int errs = chk.checker_check_program(c, prog);

        ast.ast_free(prog);
        chk.checker_free(c);
        ps.parser_free(p);
        lx.lexer_free(l);

        if (errs > 0) {
            return 99;
        }
        return 0;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

    def test_checker_detects_return_mismatch(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;
        import "src/kale_self/checker.kl" as chk;

        // fn returns void but has return 42;
        string src = "fn do_nothing() { return 42; }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);
        ast.ASTNode* prog = ps.parser_parse_program(p);

        chk.Checker* c = chk.checker_new();
        int errs = chk.checker_check_program(c, prog);

        ast.ast_free(prog);
        chk.checker_free(c);
        ps.parser_free(p);
        lx.lexer_free(l);

        if (errs > 0) {
            return 77;
        }
        return 0;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 77)

    def test_checker_function_call_and_multi_fn(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;
        import "src/kale_self/checker.kl" as chk;

        string src = "struct Point { int x; int y; } fn int double_val(int n) { return n * 2; } fn int main() { let p = 10; return double_val(p); }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);
        ast.ASTNode* prog = ps.parser_parse_program(p);

        chk.Checker* c = chk.checker_new();
        int errs = chk.checker_check_program(c, prog);

        ast.ast_free(prog);
        chk.checker_free(c);
        ps.parser_free(p);
        lx.lexer_free(l);

        if (errs == 0) {
            return 55;
        }
        return errs;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 55)

if __name__ == "__main__":
    unittest.main()
