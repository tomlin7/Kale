import unittest
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.syntax.syntax_kind import SyntaxKind
from kale.syntax.lexer import Lexer

class TestLexer(unittest.TestCase):
    def test_lex_numbers(self):
        text = SourceText("123 45.67 1e5 2.5e-3")
        lexer = Lexer(text)
        tokens = lexer.lex_all()
        self.assertEqual([t.kind for t in tokens], [
            SyntaxKind.NumberToken,
            SyntaxKind.NumberToken,
            SyntaxKind.NumberToken,
            SyntaxKind.NumberToken,
            SyntaxKind.EndOfFileToken,
        ])
        self.assertEqual(tokens[0].value, 123)
        self.assertEqual(tokens[1].value, 45.67)
        self.assertEqual(tokens[2].value, 100000.0)
        self.assertEqual(tokens[3].value, 0.0025)

    def test_lex_strings(self):
        text = SourceText('"hello \\"world\\"\\n" \'test\'')
        lexer = Lexer(text)
        tokens = lexer.lex_all()
        self.assertEqual(tokens[0].kind, SyntaxKind.StringToken)
        self.assertEqual(tokens[0].value, 'hello "world"\n')
        self.assertEqual(tokens[1].kind, SyntaxKind.StringToken)
        self.assertEqual(tokens[1].value, 'test')

    def test_lex_keywords_and_identifiers(self):
        text = SourceText("let var const if else while for return int float double myVar")
        lexer = Lexer(text)
        tokens = lexer.lex_all()
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, [
            SyntaxKind.LetKeyword,
            SyntaxKind.VarKeyword,
            SyntaxKind.ConstKeyword,
            SyntaxKind.IfKeyword,
            SyntaxKind.ElseKeyword,
            SyntaxKind.WhileKeyword,
            SyntaxKind.ForKeyword,
            SyntaxKind.ReturnKeyword,
            SyntaxKind.IntKeyword,
            SyntaxKind.FloatKeyword,
            SyntaxKind.DoubleKeyword,
            SyntaxKind.IdentifierToken,
            SyntaxKind.EndOfFileToken,
        ])
        self.assertEqual(tokens[-2].text, "myVar")

    def test_lex_operators(self):
        text = SourceText("++ -- == != <= >= << >> <<= >>= += -= *= /= **")
        lexer = Lexer(text)
        tokens = lexer.lex_all()
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, [
            SyntaxKind.PlusPlusToken,
            SyntaxKind.MinusMinusToken,
            SyntaxKind.EqualsEqualsToken,
            SyntaxKind.BangEqualsToken,
            SyntaxKind.LessOrEqualsToken,
            SyntaxKind.GreaterOrEqualsToken,
            SyntaxKind.LeftShiftToken,
            SyntaxKind.RightShiftToken,
            SyntaxKind.LeftShiftEqualsToken,
            SyntaxKind.RightShiftEqualsToken,
            SyntaxKind.PlusEqualsToken,
            SyntaxKind.MinusEqualsToken,
            SyntaxKind.StarEqualsToken,
            SyntaxKind.SlashEqualsToken,
            SyntaxKind.DoubleStarToken,
            SyntaxKind.EndOfFileToken,
        ])

    def test_lex_comments(self):
        text = SourceText("// single line\n/* multi\nline */ 42")
        lexer = Lexer(text)
        tokens = lexer.lex_all()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].kind, SyntaxKind.NumberToken)
        self.assertEqual(tokens[0].value, 42)

    def test_diagnostics_bad_char(self):
        diag = DiagnosticBag()
        text = SourceText("int a = $ + 1;")
        lexer = Lexer(text, diag)
        tokens = lexer.lex_all()
        self.assertTrue(diag.has_errors)
        self.assertIn("Bad character in input: '$'", [d.message for d in diag])

    def test_diagnostic_formatting(self):
        diag = DiagnosticBag()
        text = SourceText("int a = 12;\nint b = @;", file_name="main.kl")
        lexer = Lexer(text, diag)
        lexer.lex_all()
        formatted = text.format_diagnostic(list(diag)[0], use_color=False)
        self.assertIn("main.kl:2:9: error: Bad character in input: '@'", formatted)
        self.assertIn("int b = @;", formatted)
        self.assertIn("^", formatted)

if __name__ == "__main__":
    unittest.main()
