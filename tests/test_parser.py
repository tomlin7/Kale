import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.syntax.syntax_kind import SyntaxKind
from kale.ast.nodes import (
    BinaryExpression,
    UnaryExpression,
    LiteralExpression,
    VariableExpression,
    VariableDeclarationStatement,
    IfStatement,
    WhileStatement,
    PrintStatement,
    BlockStatement,
)
from kale.ast.printer import AstPrinter
from kale.parser.parser import Parser

class TestParser(unittest.TestCase):
    def test_precedence_multiplication_over_addition(self):
        text = SourceText("1 + 2 * 3")
        parser = Parser(text)
        expr = parser.parse_expression()
        self.assertIsInstance(expr, BinaryExpression)
        self.assertEqual(expr.operator_token.kind, SyntaxKind.PlusToken)
        self.assertEqual(expr.left.value, 1)
        self.assertIsInstance(expr.right, BinaryExpression)
        self.assertEqual(expr.right.operator_token.kind, SyntaxKind.StarToken)
        self.assertEqual(expr.right.left.value, 2)
        self.assertEqual(expr.right.right.value, 3)

    def test_right_associative_power(self):
        text = SourceText("2 ** 3 ** 4")
        parser = Parser(text)
        expr = parser.parse_expression()
        self.assertIsInstance(expr, BinaryExpression)
        self.assertEqual(expr.operator_token.kind, SyntaxKind.DoubleStarToken)
        self.assertEqual(expr.left.value, 2)
        self.assertIsInstance(expr.right, BinaryExpression)
        self.assertEqual(expr.right.left.value, 3)
        self.assertEqual(expr.right.right.value, 4)

    def test_grouping_expression(self):
        text = SourceText("(1 + 2) * 3")
        parser = Parser(text)
        expr = parser.parse_expression()
        self.assertIsInstance(expr, BinaryExpression)
        self.assertEqual(expr.operator_token.kind, SyntaxKind.StarToken)
        self.assertEqual(expr.right.value, 3)

    def test_variable_declaration_with_and_without_initializer(self):
        text = SourceText("double me;\ndouble you = 10000000;")
        parser = Parser(text)
        unit = parser.parse_compilation_unit()
        self.assertEqual(len(unit.statements), 2)
        
        stmt1 = unit.statements[0]
        self.assertIsInstance(stmt1, VariableDeclarationStatement)
        self.assertEqual(stmt1.identifier_token.text, "me")
        self.assertIsNone(stmt1.initializer)

        stmt2 = unit.statements[1]
        self.assertIsInstance(stmt2, VariableDeclarationStatement)
        self.assertEqual(stmt2.identifier_token.text, "you")
        self.assertIsNotNone(stmt2.initializer)
        self.assertEqual(stmt2.initializer.value, 10000000)

    def test_if_else_statement(self):
        text = SourceText("if (x > 0) { print(x); } else { print(0); }")
        parser = Parser(text)
        unit = parser.parse_compilation_unit()
        self.assertEqual(len(unit.statements), 1)
        if_stmt = unit.statements[0]
        self.assertIsInstance(if_stmt, IfStatement)
        self.assertIsNotNone(if_stmt.else_clause)

    def test_while_statement(self):
        text = SourceText("while (x < 10) { x = x + 1; }")
        parser = Parser(text)
        unit = parser.parse_compilation_unit()
        self.assertEqual(len(unit.statements), 1)
        while_stmt = unit.statements[0]
        self.assertIsInstance(while_stmt, WhileStatement)
        self.assertIsInstance(while_stmt.body, BlockStatement)

    def test_ast_printer(self):
        text = SourceText("int x = 42 + 1;")
        parser = Parser(text)
        unit = parser.parse_compilation_unit()
        printer = AstPrinter()
        tree_str = printer.print_node(unit)
        self.assertIn("CompilationUnit", tree_str)
        self.assertIn("VariableDeclarationStatement", tree_str)
        self.assertIn("BinaryExpression", tree_str)

    def test_syntax_error_recovery(self):
        diag = DiagnosticBag()
        text = SourceText("int a = ;\nint b = 20;", file_name="test.kl")
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertTrue(diag.has_errors)
        # Should still recover and parse 'int b = 20;'
        self.assertEqual(len(unit.statements), 2)
        self.assertEqual(unit.statements[1].identifier_token.text, "b")

if __name__ == "__main__":
    unittest.main()
