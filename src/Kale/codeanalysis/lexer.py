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
            token = Token(TokenKind.COLON, self.cur_char())
        
        elif self.cur_char() == '+':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.PLUSEQUAL, last_char + self.cur_char())
            elif self.peek() == '+':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.PLUSPLUS, last_char + self.cur_char())
            else:
                token = Token(TokenKind.PLUS, self.cur_char())
        
        elif self.cur_char() == '-':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.MINEQUAL, last_char + self.cur_char())
            elif self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.MINUSMINUS, last_char + self.cur_char())
            else:
                token = Token(TokenKind.MINUS, self.cur_char())
        
        elif self.cur_char() == '*':
            if self.peek() == '*':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.DOUBLESTAR, last_char + self.cur_char())
            elif self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.STAREQUAL, last_char + self.cur_char())
            else:
                token = Token(TokenKind.STAR, self.cur_char())
        
        elif self.cur_char() == '/':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.SLASHEQUAL, last_char + self.cur_char())
            # comments
            elif self.peek() == '/':
                while self.cur_char() != '\n':
                    self.advance()
            else:
                token = Token(TokenKind.SLASH, self.cur_char())
        
        elif self.cur_char() == '|':
            token = Token(TokenKind.VBAR, self.cur_char())
        
        
        elif self.cur_char() == '&':
            token = Token(TokenKind.AMPER, self.cur_char())
        
        
        elif self.cur_char() == '<':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.LESSEQUAL, last_char + self.cur_char())
            elif self.peek() == '<':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.LEFTSHIFT, last_char + self.cur_char())
            else:
                token = Token(TokenKind.LESS, self.cur_char())
        
        elif self.cur_char() == '>':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.GREATEREQUAL, last_char + self.cur_char())
            elif self.peek() == '>':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.RIGHTSHIFT, last_char + self.cur_char())
            else:
                token = Token(TokenKind.GREATER, self.cur_char())
        
        elif self.cur_char() == '=':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.EQEQUAL, last_char + self.cur_char())
            else:
                token = Token(TokenKind.EQUAL, self.cur_char())
        
        elif self.cur_char() == '.':
            token = Token(TokenKind.DOT)
        
        elif self.cur_char() == '%':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.PERCENTEQUAL, last_char + self.cur_char())
            else:
                token = Token(TokenKind.PERCENT, self.cur_char())
        
        elif self.cur_char() == '!':
            if self.peek() == '=':
                last_char = self.cur_char()
                self.advance()
                token = Token(TokenKind.BANGEQUAL, last_char + self.cur_char())
            else:
                token = Token(TokenKind.BANG, self.cur_char())
        
        elif self.cur_char() == '~':
            token = Token(TokenKind.TILDE, self.cur_char())
        
        elif self.cur_char() == '^':
            token = Token(TokenKind.CIRCUMFLEX, self.cur_char())
        
        # token not recognized
        else:
            token = Token(TokenKind.BADTOKEN, self.cur_char())
        
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
