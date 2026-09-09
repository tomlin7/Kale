import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.types import TypeInt, TypeDouble, TypeString, TypeBool
from kale.binding.bound_nodes import (
    BoundVariableDeclaration,
    BoundAssignmentExpression,
    BoundBinaryExpression,
    BoundBlockStatement,
)

class TestBinder(unittest.TestCase):
    def test_bind_variable_declaration_and_type(self):
        text = SourceText("int a = 10; double b = 3.14; string s = 'hi'; let d = 42;")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors)

        binder = Binder(diag)
        program = binder.bind_program(unit)
        self.assertFalse(diag.has_errors)
        self.assertEqual(len(program.statements), 4)

        stmt0 = program.statements[0]
        self.assertIsInstance(stmt0, BoundVariableDeclaration)
        self.assertEqual(stmt0.variable.type, TypeInt)

        stmt1 = program.statements[1]
        self.assertEqual(stmt1.variable.type, TypeDouble)

        stmt2 = program.statements[2]
        self.assertEqual(stmt2.variable.type, TypeString)

        stmt3 = program.statements[3]
        self.assertEqual(stmt3.variable.type, TypeInt) # deduced from literal 42

    def test_variable_redeclaration_error(self):
        text = SourceText("int x = 10;\nint x = 20;")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        messages = [d.message for d in diag]
        self.assertTrue(any("already declared" in m for m in messages))

    def test_variable_shadowing_in_inner_scope(self):
        text = SourceText("int x = 10; { int x = 20; print(x); } print(x);")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)

        self.assertFalse(diag.has_errors)
        self.assertEqual(len(program.statements), 3)
        self.assertIsInstance(program.statements[1], BoundBlockStatement)

    def test_use_before_declaration_error(self):
        text = SourceText("print(y); int y = 5;")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        messages = [d.message for d in diag]
        self.assertTrue(any("does not exist" in m for m in messages))

    def test_type_mismatch_error(self):
        text = SourceText("int x = 'invalid_string';")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        messages = [d.message for d in diag]
        self.assertTrue(any("Cannot convert" in m for m in messages))

    def test_constant_reassignment_error(self):
        text = SourceText("const pi = 3.14; pi = 3.0;")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        binder.bind_program(unit)

        self.assertTrue(diag.has_errors)
        messages = [d.message for d in diag]
        self.assertTrue(any("read-only" in m for m in messages))

    def test_numeric_promotion_in_binary_expression(self):
        text = SourceText("int a = 5; double b = 2.5; double c = a + b;")
        diag = DiagnosticBag()
        parser = Parser(text, diag)
        unit = parser.parse_compilation_unit()
        binder = Binder(diag)
        program = binder.bind_program(unit)

        self.assertFalse(diag.has_errors)
        stmt2 = program.statements[2]
        self.assertIsInstance(stmt2, BoundVariableDeclaration)
        self.assertIsInstance(stmt2.initializer, BoundBinaryExpression)
        self.assertEqual(stmt2.initializer.type, TypeDouble)

if __name__ == "__main__":
    unittest.main()
