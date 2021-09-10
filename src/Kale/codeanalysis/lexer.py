import sys

from codeanalysis.token import Token
from codeanalysis.tokenkind import TokenKind
from codeanalysis.exceptions import IllegalCharacterException

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
            token = Token(TokenKind.EOF)
        
        elif self.cur_char() in white_space:
            start = self.position
            while self.cur_char() in white_space:
                self.advance()
            length = self.position - start
            text = self.source[start:length + start]
            return Token(TokenKind.WHITESPACE, text)
            
        elif self.cur_char() == '\n':
            token = Token(TokenKind.NEWLINE)
        
        elif self.cur_char() == '\0':
            token = Token(TokenKind.EOF)
        
        elif self.cur_char() == '\"':
            self.advance()
            start_pos = self.position

            while self.cur_char() != '\"':
                if (self.cur_char() == '\r' or
                        self.cur_char() == '\n' or self.cur_char() == '\t' or
                        self.cur_char() == '\\' or self.cur_char() == '%'):
                    raise IllegalCharacterException('string')
                self.advance()

            token_text = self.source[start_pos: self.position]
            token = Token(TokenKind.STRING, token_text)
        
        elif self.cur_char().isdigit():
            start_pos = self.position
            while self.peek().isdigit():
                self.advance()
            if self.peek() == '.':
                self.advance()

                if not self.peek().isdigit():
                    raise IllegalCharacterException('number')
                while self.peek().isdigit():
                    self.advance()
            token_text = self.source[start_pos: self.position + 1]
            token = Token(TokenKind.NUMBER, token_text)
        
        elif self.cur_char().isalpha():
            start_pos = self.position
            while self.peek().isalnum():
                self.advance()

            token_text = self.source[start_pos: self.position + 1]
            keyword = Token.check_keyword(token_text.upper())
            if keyword is None:
                token = Token(TokenKind.IDENT, token_text)
            # Keywords
            else:
                token = Token(keyword)

        # Punctuators
        # ----------------------------------------------------------------

        elif self.cur_char() == '(':
            token = Token(TokenKind.LPAR)
        
        elif self.cur_char() == ')':
            token = Token(TokenKind.RPAR)
        
        elif self.cur_char() == '[':
            token = Token(TokenKind.LSQB)
        
        elif self.cur_char() == ']':
            token = Token(TokenKind.RSQB)
        
        elif self.cur_char() == '{':
            token = Token(TokenKind.LBRACE)
        
        elif self.cur_char() == '}':
            token = Token(TokenKind.RBRACE)
        
        elif self.cur_char() == ',':
            token = Token(TokenKind.COMMA)
        
        elif self.cur_char() == ';':
            token = Token(TokenKind.SEMI)

        # Operators
        # ----------------------------------------------------------------

        elif self.cur_char() == ':':
            token = Token(TokenKind.COLON)
        
        elif self.cur_char() == '+':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.PLUSEQUAL)
            elif self.peek() == '+':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.PLUSPLUS)
            else:
                token = Token(TokenKind.PLUS)
        
        elif self.cur_char() == '-':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.MINEQUAL)
            elif self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.MINUSMINUS)
            else:
                token = Token(TokenKind.MINUS)
        
        elif self.cur_char() == '*':
            if self.peek() == '*':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.DOUBLESTAR)
            elif self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.STAREQUAL)
            else:
                token = Token(TokenKind.STAR)
        
        elif self.cur_char() == '/':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.SLASHEQUAL)
            # comments
            elif self.peek() == '/':
                while self.cur_char() != '\n':
                    self.advance()
            else:
                token = Token(TokenKind.SLASH)
        
        elif self.cur_char() == '|':
            token = Token(TokenKind.VBAR)
        
        
        elif self.cur_char() == '&':
            token = Token(TokenKind.AMPER)
        
        
        elif self.cur_char() == '<':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.LESSEQUAL)
            elif self.peek() == '<':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.LEFTSHIFT)
            else:
                token = Token(TokenKind.LESS)
        
        elif self.cur_char() == '>':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.GREATEREQUAL)
            elif self.peek() == '>':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.RIGHTSHIFT)
            else:
                token = Token(TokenKind.GREATER)
        
        elif self.cur_char() == '=':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.EQEQUAL)
            else:
                token = Token(TokenKind.EQUAL)
        
        elif self.cur_char() == '.':
            token = Token(TokenKind.DOT)
        
        elif self.cur_char() == '%':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.PERCENTEQUAL)
            else:
                token = Token(TokenKind.PERCENT)
        
        elif self.cur_char() == '!':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(last_char + TokenKind.BANGEQUAL)
            else:
                token = Token(TokenKind.BANG)
        
        elif self.cur_char() == '~':
            token = Token(TokenKind.TILDE)
        
        elif self.cur_char() == '^':
            token = Token(TokenKind.CIRCUMFLEX)
        
        # token not recognized
        else:
            token = Token(TokenKind.BADTOKEN)
        
        self.advance()
        return token

    def lex(self):
        token_list = []
        while True:
            token = self.next_token()
            if token.kind == TokenKind.EOF:
                token_list.append(token)
                break
            if token.kind == TokenKind.BADTOKEN:
                self.abort("Error: Invalid Token")
            if token.kind not in [TokenKind.NEWLINE, TokenKind.WHITESPACE]:
                token_list.append(token)

        for x in token_list:
            print(x)

        return token_list
