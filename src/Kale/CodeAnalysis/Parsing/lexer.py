from loguru import logger

from CodeAnalysis.Syntax.syntaxtoken import SyntaxToken
from CodeAnalysis.Syntax.syntaxkind import SyntaxKind

from CodeAnalysis.Exceptions.illegalcharacter import IllegalCharacterException
from CodeAnalysis.Exceptions.invalidtoken import InvalidTokenException


class Lexer:
    def __init__(self, text):
        self.source = text
        self.position = 0

    def cur_char(self):
        if self.position >= len(self.source):
            return '\0'
        return self.source[self.position]

    def peek(self):
        if self.position + 1 >= len(self.source):
            return '\0'
        return self.source[self.position + 1]

    def advance(self, offset=0):
        self.position += 1 + offset

    def next_token(self):
        white_space = [' ', '\t', '\r']
        token = None

        # Literals
        # ----------------------------------------------------------------

        if self.position >= len(self.source):
            token = SyntaxToken(SyntaxKind.EndOfFileToken)

        elif self.cur_char() in white_space:
            start = self.position
            while self.cur_char() in white_space:
                self.advance()
            length = self.position - start
            text = self.source[start:length + start]
            return SyntaxToken(SyntaxKind.WhiteSpaceToken, text)

        elif self.cur_char() == '\n':
            token = SyntaxToken(SyntaxKind.NewLineToken)

        elif self.cur_char() == '\"':
            self.advance()
            start_pos = self.position

            while self.cur_char() not in ['\"', '\0']:
                if self.cur_char() in ['\r', '\n', '\t', '\\', '%']:
                    # logger.error(f'Illegal character {self.cur_char()}')
                    # exit(1)
                    raise IllegalCharacterException(f'at {self.cur_char()}')

                self.advance()

            token_text = self.source[start_pos: self.position]
            token = SyntaxToken(SyntaxKind.StringToken, token_text)
        
        elif self.cur_char() == '\'':
            self.advance()
            start_pos = self.position

            while self.cur_char() not in ['\'', '\0']:
                if self.cur_char() in ['\r', '\n', '\t', '\\', '%']:
                    # logger.error(f'Illegal character {self.cur_char()}')
                    # exit(1)
                    raise IllegalCharacterException(f'at {self.cur_char()}')

                self.advance()

            token_text = self.source[start_pos: self.position]
            token = SyntaxToken(SyntaxKind.StringToken, token_text)

        elif self.cur_char().isdigit():
            start_pos = self.position
            while self.peek().isdigit():
                self.advance()
            if self.peek() == '.':
                self.advance()

                if not self.peek().isdigit():
                    # logger.error(f'Invalid number {self.source[start_pos: self.position + 1]}')
                    # exit(0)
                    raise IllegalCharacterException(f'at {self.cur_char()}')
                
                while self.peek().isdigit():
                    self.advance()
            token_text = self.source[start_pos: self.position + 1]
            token = SyntaxToken(SyntaxKind.NumberToken, token_text)

        elif self.cur_char().isalpha():
            start_pos = self.position
            while self.peek().isalnum():
                self.advance()

            token_text = self.source[start_pos: self.position + 1]
            keyword = SyntaxToken().check_keyword(token_text)
            if keyword is None:
                token = SyntaxToken(SyntaxKind.IdentifierToken, token_text)
            # Keywords
            else:
                token = SyntaxToken(keyword)

        # Punctuators
        # ----------------------------------------------------------------

        elif self.cur_char() == '(':
            token = SyntaxToken(SyntaxKind.OpenParenthesisToken)

        elif self.cur_char() == ')':
            token = SyntaxToken(SyntaxKind.CloseParenthesisToken)

        elif self.cur_char() == '[':
            token = SyntaxToken(SyntaxKind.OpenBracketsToken)

        elif self.cur_char() == ']':
            token = SyntaxToken(SyntaxKind.CloseBracketsToken)

        elif self.cur_char() == '{':
            token = SyntaxToken(SyntaxKind.OpenBraceToken)

        elif self.cur_char() == '}':
            token = SyntaxToken(SyntaxKind.CloseBraceToken)

        elif self.cur_char() == ',':
            token = SyntaxToken(SyntaxKind.CommaToken)

        elif self.cur_char() == ';':
            token = SyntaxToken(SyntaxKind.SemicolonToken)

        # Operators
        # ----------------------------------------------------------------

        elif self.cur_char() == ':':
            token = SyntaxToken(SyntaxKind.ColonToken, self.cur_char())

        elif self.cur_char() == '+':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.PlusEqualsToken, last_char + self.cur_char())
            elif self.peek() == '+':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.PlusPlusToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.PlusToken, self.cur_char())

        elif self.cur_char() == '-':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.MinusEqualsToken, last_char + self.cur_char())
            elif self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.MinusMinusToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.MinusToken, self.cur_char())

        elif self.cur_char() == '*':
            if self.peek() == '*':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.DoubleStarToken, last_char + self.cur_char())
            elif self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.StarEqualsToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.StartToken, self.cur_char())

        elif self.cur_char() == '/':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.SlashEqualsToken, last_char + self.cur_char())
            # comments
            elif self.peek() == '/':
                start = self.position
                while self.cur_char() not in ['\n', '\0']:
                    self.advance()
                length = self.position - start
                text = self.source[start:length + start]
                token = SyntaxToken(SyntaxKind.Comments, text)
            else:
                token = SyntaxToken(SyntaxKind.SlashToken, self.cur_char())

        elif self.cur_char() == '|':
            token = SyntaxToken(SyntaxKind.PipeToken, self.cur_char())

        elif self.cur_char() == '&':
            token = SyntaxToken(SyntaxKind.AmpersandToken, self.cur_char())

        elif self.cur_char() == '<':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.LessOrEqualsToken, last_char + self.cur_char())
            elif self.peek() == '<':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.LeftShiftToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.LessToken, self.cur_char())

        elif self.cur_char() == '>':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.GreaterOrEqualsToken, last_char + self.cur_char())
            elif self.peek() == '>':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.RightShiftToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.GreaterToken, self.cur_char())

        elif self.cur_char() == '=':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.EqualsEqualsToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.EqualsToken, self.cur_char())

        elif self.cur_char() == '.':
            token = SyntaxToken(SyntaxKind.DotToken)

        elif self.cur_char() == '%':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.PercentEqualsToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.PercentToken, self.cur_char())

        elif self.cur_char() == '!':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = SyntaxToken(SyntaxKind.BangEqualsToken, last_char + self.cur_char())
            else:
                token = SyntaxToken(SyntaxKind.BangToken, self.cur_char())

        elif self.cur_char() == '~':
            token = SyntaxToken(SyntaxKind.TildeToken, self.cur_char())

        elif self.cur_char() == '^':
            token = SyntaxToken(SyntaxKind.HatToken, self.cur_char())

        # illegal token
        else:
            token = SyntaxToken(SyntaxKind.BadToken, self.cur_char())

        self.advance()
        return token

    def lex(self):
        token_list = []
        while True:
            token = self.next_token()
            if token.kind == SyntaxKind.EndOfFileToken:
                token_list.append(token)
                break
            if token.kind == SyntaxKind.BadToken:
                raise InvalidTokenException(token.value)
            if token.kind not in [SyntaxKind.NewLineToken, SyntaxKind.WhiteSpaceToken, SyntaxKind.Comments]:
                token_list.append(token)

        for x in token_list:
            print(x)

        return token_list
