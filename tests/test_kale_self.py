import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestKaleSelfHosting(unittest.TestCase):
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

    def test_kale_self_lexer_basic(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;

        string src = "fn add(int a, int b) { return a + b; }";
        lx.Lexer* l = lx.lexer_new(src);

        tok.Token* t0 = lx.lexer_next_token(l); // fn
        if (t0->kind != tok.TOK_FN()) { return 1; }

        tok.Token* t1 = lx.lexer_next_token(l); // add
        if (t1->kind != tok.TOK_IDENT()) { return 2; }

        tok.Token* t2 = lx.lexer_next_token(l); // (
        if (t2->kind != tok.TOK_LPAREN()) { return 3; }

        tok.Token* t3 = lx.lexer_next_token(l); // int (ident)
        if (t3->kind != tok.TOK_IDENT()) { return 4; }

        tok.Token* t4 = lx.lexer_next_token(l); // a
        if (t4->kind != tok.TOK_IDENT()) { return 5; }

        tok.Token* t5 = lx.lexer_next_token(l); // ,
        if (t5->kind != tok.TOK_COMMA()) { return 6; }

        lx.lexer_free(l);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kale_self_lexer_numbers_and_operators(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;

        string src = "1234 56.78f == != <= >= -> && || \\"hello\\"";
        lx.Lexer* l = lx.lexer_new(src);

        tok.Token* t0 = lx.lexer_next_token(l);
        if (t0->kind != tok.TOK_INT() || t0->int_val != 1234) { return 1; }

        tok.Token* t1 = lx.lexer_next_token(l);
        if (t1->kind != tok.TOK_FLOAT()) { return 2; }

        tok.Token* t2 = lx.lexer_next_token(l);
        if (t2->kind != tok.TOK_EQEQ()) { return 3; }

        tok.Token* t3 = lx.lexer_next_token(l);
        if (t3->kind != tok.TOK_NEQ()) { return 4; }

        tok.Token* t4 = lx.lexer_next_token(l);
        if (t4->kind != tok.TOK_LTE()) { return 5; }

        tok.Token* t5 = lx.lexer_next_token(l);
        if (t5->kind != tok.TOK_GTE()) { return 6; }

        tok.Token* t6 = lx.lexer_next_token(l);
        if (t6->kind != tok.TOK_ARROW()) { return 7; }

        tok.Token* t7 = lx.lexer_next_token(l);
        if (t7->kind != tok.TOK_ANDAND()) { return 8; }

        tok.Token* t8 = lx.lexer_next_token(l);
        if (t8->kind != tok.TOK_OROR()) { return 9; }

        tok.Token* t9 = lx.lexer_next_token(l);
        if (t9->kind != tok.TOK_STRING()) { return 10; }

        tok.Token* t10 = lx.lexer_next_token(l);
        if (t10->kind != tok.TOK_EOF()) { return 11; }

        lx.lexer_free(l);
        return 77;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 77)

    def test_kale_self_ast_construction(self):
        code = """
        import "src/kale_self/ast.kl" as ast;

        ast.ASTNode* lit1 = ast.ast_literal(10);
        ast.ASTNode* lit2 = ast.ast_literal(20);
        ast.ASTNode* add = ast.ast_binary(30, lit1, lit2); // '+'

        if (add->kind != ast.AST_BINARY()) { return 1; }
        if (add->left->int_val != 10) { return 2; }
        if (add->right->int_val != 20) { return 3; }

        ast.ASTNode* ret_stmt = ast.ast_return(add);
        if (ret_stmt->kind != ast.AST_RETURN()) { return 4; }

        ast.ast_free(ret_stmt);
        return 99;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

    def test_kale_self_parser_expression_and_statement(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;

        string src = "return 10 + 20 * 3;";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);

        ast.ASTNode* stmt = ps.parser_parse_statement(p);
        if (stmt == (ast.ASTNode*)0) { return 1; }
        if (stmt->kind != ast.AST_RETURN()) { return 2; }

        ast.ASTNode* expr = stmt->left;
        if (expr->kind != ast.AST_BINARY()) { return 3; } // '+'
        if (expr->op != tok.TOK_PLUS()) { return 4; }

        ast.ASTNode* lhs = expr->left;
        if (lhs->kind != ast.AST_LITERAL() || lhs->int_val != 10) { return 5; }

        ast.ASTNode* rhs = expr->right; // 20 * 3
        if (rhs->kind != ast.AST_BINARY() || rhs->op != tok.TOK_STAR()) { return 6; }
        if (rhs->left->int_val != 20 || rhs->right->int_val != 3) { return 7; }

        ast.ast_free(stmt);
        ps.parser_free(p);
        lx.lexer_free(l);
        return 123;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 123)

    def test_kale_self_parser_program_and_fn(self):
        code = """
        import "src/kale_self/token.kl" as tok;
        import "src/kale_self/lexer.kl" as lx;
        import "src/kale_self/ast.kl" as ast;
        import "src/kale_self/parser.kl" as ps;

        string src = "fn calculate(int x, int y) { if (x > 0) { return x + y; } return 0; }";
        lx.Lexer* l = lx.lexer_new(src);
        ps.Parser* p = ps.parser_new(l);

        ast.ASTNode* prog = ps.parser_parse_program(p);
        if (prog == (ast.ASTNode*)0) { return 1; }
        if (prog->kind != ast.AST_PROGRAM()) { return 2; }

        ast.ASTNode* fn_node = prog->body;
        if (fn_node == (ast.ASTNode*)0 || fn_node->kind != ast.AST_FN_DECL()) { return 3; }

        // Parameters
        ast.ASTNode* p1 = fn_node->left;
        if (p1 == (ast.ASTNode*)0 || p1->kind != ast.AST_PARAM()) { return 4; }
        ast.ASTNode* p2 = p1->next;
        if (p2 == (ast.ASTNode*)0 || p2->kind != ast.AST_PARAM()) { return 5; }

        // Body block
        ast.ASTNode* body = fn_node->body;
        if (body == (ast.ASTNode*)0 || body->kind != ast.AST_BLOCK()) { return 6; }

        // First stmt in body: if
        ast.ASTNode* if_stmt = body->body;
        if (if_stmt == (ast.ASTNode*)0 || if_stmt->kind != ast.AST_IF()) { return 7; }

        ast.ast_free(prog);
        ps.parser_free(p);
        lx.lexer_free(l);
        return 246;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 246)

if __name__ == "__main__":
    unittest.main()
