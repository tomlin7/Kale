from ..diagnostics.text_span import TextSpan
from ..diagnostics.source_text import SourceText
from ..diagnostics.diagnostic_bag import DiagnosticBag
from .syntax_kind import SyntaxKind
from .syntax_token import SyntaxToken
from .syntax_facts import get_keyword_kind

class Lexer:
    """Tokenizes source code into a stream of SyntaxToken instances."""
    def __init__(self, source_text: SourceText, diagnostics: DiagnosticBag | None = None):
        self.source_text = source_text
        self.diagnostics = diagnostics if diagnostics is not None else DiagnosticBag()
        self._position = 0

    @property
    def _cur_char(self) -> str:
        return self._peek(0)

    def _peek(self, offset: int = 0) -> str:
        idx = self._position + offset
        if idx >= len(self.source_text):
            return '\0'
        return self.source_text[idx]

    def _advance(self, count: int = 1):
        self._position += count

    def next_token(self) -> SyntaxToken:
        """Scans and returns the next token from source text."""
        # End of file
        if self._position >= len(self.source_text):
            return SyntaxToken(SyntaxKind.EndOfFileToken, TextSpan(self._position, 0), None, "")

        start = self._position
        c = self._cur_char

        # Whitespace
        if c in (' ', '\t', '\r'):
            while self._cur_char in (' ', '\t', '\r'):
                self._advance()
            length = self._position - start
            return SyntaxToken(SyntaxKind.WhitespaceTrivia, TextSpan(start, length), None, self.source_text.text[start:self._position])

        # Newline
        if c == '\n':
            self._advance()
            return SyntaxToken(SyntaxKind.NewLineTrivia, TextSpan(start, 1), None, "\n")

        # Comments
        if c == '/' and self._peek(1) == '/':
            self._advance(2)
            while self._cur_char not in ('\n', '\0'):
                self._advance()
            length = self._position - start
            return SyntaxToken(SyntaxKind.CommentTrivia, TextSpan(start, length), None, self.source_text.text[start:self._position])

        if c == '/' and self._peek(1) == '*':
            self._advance(2)
            while True:
                if self._cur_char == '\0':
                    self.diagnostics.report(TextSpan(start, self._position - start), "Unterminated block comment.")
                    break
                if self._cur_char == '*' and self._peek(1) == '/':
                    self._advance(2)
                    break
                self._advance()
            length = self._position - start
            return SyntaxToken(SyntaxKind.CommentTrivia, TextSpan(start, length), None, self.source_text.text[start:self._position])

        # Numbers
        if c.isdigit():
            return self._lex_number(start)

        # Identifiers and keywords
        if c.isalpha() or c == '_':
            while self._cur_char.isalnum() or self._cur_char == '_':
                self._advance()
            length = self._position - start
            text = self.source_text.text[start:self._position]
            kind = get_keyword_kind(text)
            if kind is None:
                kind = SyntaxKind.IdentifierToken
                return SyntaxToken(kind, TextSpan(start, length), text, text)
            
            # Keyword values
            val = None
            if kind == SyntaxKind.TrueKeyword:
                val = True
            elif kind == SyntaxKind.FalseKeyword:
                val = False
            return SyntaxToken(kind, TextSpan(start, length), val, text)

        # String literals
        if c in ('"', "'"):
            return self._lex_string(start, quote_char=c)

        # Multi-character and single-character operators
        # 3-character operators / punctuators: <<=, >>=, ...
        if c == '<' and self._peek(1) == '<' and self._peek(2) == '=':
            self._advance(3)
            return SyntaxToken(SyntaxKind.LeftShiftEqualsToken, TextSpan(start, 3), None, "<<=")
        if c == '>' and self._peek(1) == '>' and self._peek(2) == '=':
            self._advance(3)
            return SyntaxToken(SyntaxKind.RightShiftEqualsToken, TextSpan(start, 3), None, ">>=")
        if c == '.' and self._peek(1) == '.' and self._peek(2) == '.':
            self._advance(3)
            return SyntaxToken(SyntaxKind.DotDotDotToken, TextSpan(start, 3), None, "...")

        # 2-character operators
        two_char = c + self._peek(1)
        two_char_map = {
            "==": SyntaxKind.EqualsEqualsToken,
            "!=": SyntaxKind.BangEqualsToken,
            "<=": SyntaxKind.LessOrEqualsToken,
            ">=": SyntaxKind.GreaterOrEqualsToken,
            "&&": SyntaxKind.AmpersandAmpersandToken,
            "||": SyntaxKind.PipePipeToken,
            "<<": SyntaxKind.LeftShiftToken,
            ">>": SyntaxKind.RightShiftToken,
            "**": SyntaxKind.DoubleStarToken,
            "++": SyntaxKind.PlusPlusToken,
            "--": SyntaxKind.MinusMinusToken,
            "+=": SyntaxKind.PlusEqualsToken,
            "-=": SyntaxKind.MinusEqualsToken,
            "*=": SyntaxKind.StarEqualsToken,
            "/=": SyntaxKind.SlashEqualsToken,
            "%=": SyntaxKind.PercentEqualsToken,
            "&=": SyntaxKind.AmpersandEqualsToken,
            "|=": SyntaxKind.PipeEqualsToken,
            "^=": SyntaxKind.HatEqualsToken,
            "->": SyntaxKind.ArrowToken,
        }
        if two_char in two_char_map:
            self._advance(2)
            return SyntaxToken(two_char_map[two_char], TextSpan(start, 2), None, two_char)

        # Single-character tokens
        single_char_map = {
            '(': SyntaxKind.OpenParenthesisToken,
            ')': SyntaxKind.CloseParenthesisToken,
            '{': SyntaxKind.OpenBraceToken,
            '}': SyntaxKind.CloseBraceToken,
            '[': SyntaxKind.OpenBracketToken,
            ']': SyntaxKind.CloseBracketToken,
            ',': SyntaxKind.CommaToken,
            ';': SyntaxKind.SemicolonToken,
            ':': SyntaxKind.ColonToken,
            '.': SyntaxKind.DotToken,
            '+': SyntaxKind.PlusToken,
            '-': SyntaxKind.MinusToken,
            '*': SyntaxKind.StarToken,
            '/': SyntaxKind.SlashToken,
            '%': SyntaxKind.PercentToken,
            '<': SyntaxKind.LessToken,
            '>': SyntaxKind.GreaterToken,
            '=': SyntaxKind.EqualsToken,
            '!': SyntaxKind.BangToken,
            '&': SyntaxKind.AmpersandToken,
            '|': SyntaxKind.PipeToken,
            '^': SyntaxKind.CaretToken,
            '~': SyntaxKind.TildeToken,
        }
        if c in single_char_map:
            self._advance(1)
            return SyntaxToken(single_char_map[c], TextSpan(start, 1), None, c)

        # Bad token / unrecognized character
        self._advance(1)
        self.diagnostics.report_bad_character(TextSpan(start, 1), c)
        return SyntaxToken(SyntaxKind.BadToken, TextSpan(start, 1), None, c)

    def _lex_number(self, start: int) -> SyntaxToken:
        has_dot = False
        has_exponent = False

        while self._cur_char.isdigit():
            self._advance()

        if self._cur_char == '.' and self._peek(1).isdigit():
            has_dot = True
            self._advance() # consume '.'
            while self._cur_char.isdigit():
                self._advance()

        if self._cur_char in ('e', 'E'):
            has_exponent = True
            self._advance()
            if self._cur_char in ('+', '-'):
                self._advance()
            if not self._cur_char.isdigit():
                length = self._position - start
                text = self.source_text.text[start:self._position]
                self.diagnostics.report_invalid_number(TextSpan(start, length), text)
                return SyntaxToken(SyntaxKind.BadToken, TextSpan(start, length), None, text)
            while self._cur_char.isdigit():
                self._advance()

        has_f_suffix = False
        if self._cur_char in ('f', 'F'):
            has_f_suffix = True
            self._advance()

        length = self._position - start
        text = self.source_text.text[start:self._position]

        try:
            if has_dot or has_exponent or has_f_suffix:
                clean_text = text[:-1] if has_f_suffix else text
                value = float(clean_text)
            else:
                value = int(text)
            return SyntaxToken(SyntaxKind.NumberToken, TextSpan(start, length), value, text)
        except ValueError:
            self.diagnostics.report_invalid_number(TextSpan(start, length), text)
            return SyntaxToken(SyntaxKind.BadToken, TextSpan(start, length), None, text)

    def _lex_string(self, start: int, quote_char: str) -> SyntaxToken:
        self._advance() # skip opening quote
        chars = []
        is_terminated = False

        while True:
            c = self._cur_char
            if c == '\0' or c == '\n':
                break
            if c == quote_char:
                self._advance()
                is_terminated = True
                break
            if c == '\\':
                self._advance()
                esc = self._cur_char
                if esc == 'n':
                    chars.append('\n')
                    self._advance()
                elif esc == 'r':
                    chars.append('\r')
                    self._advance()
                elif esc == 't':
                    chars.append('\t')
                    self._advance()
                elif esc == '\\':
                    chars.append('\\')
                    self._advance()
                elif esc == '"':
                    chars.append('"')
                    self._advance()
                elif esc == "'":
                    chars.append("'")
                    self._advance()
                elif esc == '0':
                    chars.append('\0')
                    self._advance()
                else:
                    self.diagnostics.report_invalid_escape_sequence(TextSpan(self._position - 1, 2), esc)
                    chars.append(esc)
                    self._advance()
            else:
                chars.append(c)
                self._advance()

        length = self._position - start
        raw_text = self.source_text.text[start:self._position]

        if not is_terminated:
            self.diagnostics.report_unterminated_string(TextSpan(start, length))
            return SyntaxToken(SyntaxKind.BadToken, TextSpan(start, length), None, raw_text)

        value = "".join(chars)
        if quote_char == "'" and len(value) == 1:
            # Single character literal
            char_val = ord(value[0])
            return SyntaxToken(SyntaxKind.CharToken, TextSpan(start, length), char_val, raw_text)
        return SyntaxToken(SyntaxKind.StringToken, TextSpan(start, length), value, raw_text)

    def lex_all(self, include_trivia: bool = False) -> list[SyntaxToken]:
        """Lexes entire source into a list of tokens terminating with EndOfFileToken."""
        tokens = []
        trivia_kinds = {SyntaxKind.WhitespaceTrivia, SyntaxKind.NewLineTrivia, SyntaxKind.CommentTrivia}
        while True:
            tok = self.next_token()
            if include_trivia or tok.kind not in trivia_kinds:
                tokens.append(tok)
            if tok.kind == SyntaxKind.EndOfFileToken:
                break
        return tokens
