import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestKaleSelfCodegen(unittest.TestCase):
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

    def test_emitter_basic_primitives(self):
        code = """
        import "src/kale_self/codegen.kl" as cg;
        extern int strcmp(string s1, string s2);

        cg.CodeEmitter* e = cg.emitter_new();
        cg.emitter_emit(e, "hello");
        cg.emitter_emit_char(e, (char)32); // ' '
        cg.emitter_emit_int(e, 123);
        cg.emitter_emit_line(e, ";");

        int len = cg.emitter_len(e);
        if (len <= 0) { return 1; }

        string out = cg.emitter_to_string(e);
        cg.emitter_free(e);

        if (strcmp(out, "hello 123;\\n") == 0) {
            return 42;
        }
        return 2;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_emitter_expressions(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/codegen.kl" as cg;
        extern int strcmp(string s1, string s2);

        // Build AST for: (a + 10)
        ast.ASTNode* a = ast.ast_ident("a");
        ast.ASTNode* lit = ast.ast_literal(10);
        ast.ASTNode* bin = ast.ast_binary(tok.TOK_PLUS(), a, lit);

        cg.CodeEmitter* e = cg.emitter_new();
        cg.emitter_emit_expr(e, bin);
        string res_str = cg.emitter_to_string(e);

        ast.ast_free(bin);
        cg.emitter_free(e);

        if (strcmp(res_str, "(a + 10)") == 0) {
            return 77;
        }
        return 1;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 77)

    def test_emitter_function_call_and_assign(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/codegen.kl" as cg;
        extern int strcmp(string s1, string s2);

        // foo(1, 2)
        ast.ASTNode* arg1 = ast.ast_literal(1);
        ast.ASTNode* arg2 = ast.ast_literal(2);
        arg1->next = arg2;
        ast.ASTNode* call = ast.ast_call("foo", arg1);

        cg.CodeEmitter* e = cg.emitter_new();
        cg.emitter_emit_expr(e, call);
        string res_str = cg.emitter_to_string(e);

        ast.ast_free(call);
        cg.emitter_free(e);

        if (strcmp(res_str, "foo(1, 2)") == 0) {
            return 88;
        }
        return 1;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 88)

    def test_emitter_statement_var_decl_and_return(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/codegen.kl" as cg;
        extern int strcmp(string s1, string s2);

        // int x = 42;
        ast.ASTNode* lit = ast.ast_literal(42);
        ast.ASTNode* decl = ast.ast_var_decl("int", "x", lit);

        cg.CodeEmitter* e = cg.emitter_new();
        cg.emitter_emit_stmt(e, decl);
        string res_str = cg.emitter_to_string(e);

        ast.ast_free(decl);
        cg.emitter_free(e);

        if (strcmp(res_str, "int64_t x = 42;\\n") == 0) {
            return 99;
        }
        return 1;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

    def test_emitter_full_pipeline_parse_and_codegen(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;
        import "src/kale_self/checker.kl" as chk;
        import "src/kale_self/codegen.kl" as cg;
        extern int strstr(string haystack, string needle);

        string src = "fn int add(int a, int b) { return a + b; }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);
        ast.ASTNode* prog = ps.parser_parse_program(p);

        chk.Checker* c = chk.checker_new();
        int errs = chk.checker_check_program(c, prog);
        if (errs > 0) {
            ast.ast_free(prog);
            chk.checker_free(c);
            ps.parser_free(p);
            lx.lexer_free(l);
            return 1;
        }

        cg.CodeEmitter* emitter = cg.emitter_new();
        cg.emitter_emit_program(emitter, prog);
        int out_len = cg.emitter_len(emitter);
        string c_code = cg.emitter_to_string(emitter);

        ast.ast_free(prog);
        chk.checker_free(c);
        ps.parser_free(p);
        lx.lexer_free(l);
        cg.emitter_free(emitter);

        if (out_len > 0) {
            return 100;
        }
        return 2;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 100)

if __name__ == "__main__":
    unittest.main()
