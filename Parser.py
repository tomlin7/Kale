import sys
from TokenKind import TokenKind
# from termcolor import cprint


class Parser:
    def __init__(self, token_list, emitter, dev=False):
        self.token_list = token_list
        self.position = -1
        # self.emitter = emitter
        self.dev = dev

        # Sets the current token to the first token taken from the input
        # ----
        self.symbols = set()
        self.labels_declared = set()
        self.labels_gotoed = set()  # goto'ed
        # ----

        # tokens
        # ----
        self.cur_token = None
        # ----

        self.advance()
        
    def check_token(self, kind):
        """
        Checks whether passed token kind matches the current token kind.
        """

        return kind == self.cur_token.kind

    def peek(self, kind):
        """
        Checks whether passed token kind matches the next token.
        """

        return self.token_list[self.position + 1]

    def match(self, kind):
        """
        Matches the current token kind to the passed token kind.
        
        Exceptions: Raises an error if the token kind doesn't match.
        """

        if not self.check_token(kind):
            self.abort("Expected " + kind.name + ", got " + self.cur_token.kind.name)
        self.advance()
    
    def advance(self, offset=0):
        """
        Sets the current token to the next token.
        """
        self.position += 1 + offset
        if self.position < len(self.token_list):
            self.cur_token = self.token_list[self.position]

    def is_comparison_operator(self):
        """
        Checks whether the current token is a comparison operator.
        """

        return (
            self.check_token(TokenKind.GREATER) or self.check_token(TokenKind.GREATEREQUAL) or
            self.check_token(TokenKind.LESS) or self.check_token(TokenKind.LESSEQUAL) or
            self.check_token(TokenKind.EQEQUAL) or self.check_token(TokenKind.BANGEQUAL)
        )

    def abort(self, message):
        """
        Aborts the program with the passed message.
        """

        # cprint("Error: " + message, 'red')
        # sys.exit(0)
        sys.exit("Error: " + message)

    # Production rules.
    def program(self):
        """
        Program entry point
        """
        if self.dev:
            print("Program")

        # self.emitter.add_header("#include <stdio.h>")
        # self.emitter.add_header("int main(void){")

        # while self.check_token(TokenKind.NEWLINE):
        #     self.advance()

        while not self.check_token(TokenKind.EOF):
            self.statement()

        # self.emitter.emit_line("return 0;")
        # self.emitter.emit_line("}")

        for label in self.labels_gotoed:
            if label not in self.labels_declared:
                self.abort("Attempting to goto to undeclared label: " + label)

    def statement(self):
        """
        Statements Parser
        """

        if self.check_token(TokenKind.PRINT):
            """
            Print Statement
            
            Syntax: 
                1.  print(STRING)
                2.  print(EXPRESSION)
            """
            if self.dev:
                print("Print-Statement")

            self.advance()
            self.match(TokenKind.LPAR)

            if self.check_token(TokenKind.STRING):
                # self.emitter.emit_line("printf(\"{self.cur_token.value}\\n\");")
                self.advance()
            else:
                # self.emitter.emit_line("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                # self.emitter.emit_line("));")
            self.match(TokenKind.RPAR)
        
        elif self.check_token(TokenKind.IF):
            """
            If/If-else Statement
            
            Syntax: 
                1.  if(EXPRESSION) 
                    { 
                        STATEMENTS 
                    }
                    
                2.  if (COMPARISON) 
                    {
                        STATEMENT
                    } else {
                        STATEMENT            
                    }
            """
            if self.dev:
                print("If-Statement")

            self.advance()

            # First part
            # ----
            self.match(TokenKind.LPAR)
            # self.emitter.emit("if(")

            self.comparison()
            self.match(TokenKind.RPAR)
            # ----
            
            # Second part
            # ----
            self.match(TokenKind.LBRACE)
            # self.emitter.emit_line("){")
            while not self.check_token(TokenKind.RBRACE):
                self.statement()

            self.match(TokenKind.RBRACE)
            # ----

            # Third optional part
            # ----
            if self.check_token(TokenKind.ELSE):
                if self.dev:
                    print("Else-Statement")

                self.advance()
                self.match(TokenKind.LBRACE)
                
                while not self.check_token(TokenKind.RBRACE):
                    self.statement()
                    
            self.match(TokenKind.RBRACE)
            # self.emitter.emit_line("}")
            # ----

        elif self.check_token(TokenKind.WHILE):
            """
            While Statement

            Syntax:
                1.  while(EXPRESSION)
                    {
                        STATEMENTS
                    }
            """
            if self.dev:
                print("While-Statement")
            
            self.advance()

            # First part
            # ----
            self.match(TokenKind.LPAR)
            # self.emitter.emit("while(")
            self.comparison()
            self.match(TokenKind.RPAR)
            # ----

            # Second part
            # ----
            self.match(TokenKind.LBRACE)
            
            # self.emitter.emit_line("){")
            while not self.check_token(TokenKind.RBRACE):
                self.statement()
            
            self.match(TokenKind.RBRACE)
            # self.emitter.emit_line("}")
            # ----
            
        elif self.check_token(TokenKind.LABEL):
            """
            Label Statement

            Syntax:
                1.  label IDENTIFIER:
            """
            if self.dev:
                print("Label-Statement")

            self.advance()

            # ----
            if self.cur_token.value in self.labels_declared:
                self.abort(f"Label already exists: {self.cur_token.value}")
            self.labels_declared.add(self.cur_token.value)

            # self.emitter.emit_line(self.cur_token.value + ":")

            self.match(TokenKind.IDENT)
            self.match(TokenKind.COLON)
            # ----

        elif self.check_token(TokenKind.GOTO):
            """
            Goto Statement

            Syntax:
                1.  goto IDENTIFIER
            """
            if self.dev:
                print("Goto-Statement")
    
            self.advance()
            
            # ----
            self.labels_gotoed.add(self.cur_token.value)
            
            self.match(TokenKind.IDENT)
            # self.emitter.emit_line(f"goto {self.cur_token.value};")
            # ----

        elif self.check_token(TokenKind.LET):
            """
            Let Statement

            Syntax:
                1.  let IDENTIFIER = EXPRESSION
            """
            if self.dev:
                print("Let-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
                # self.emitter.add_header(f"auto {self.cur_token.value};")
            else:
                self.abort(f"A local variable named '{self.cur_token.value}' is already defined in this scope")

            # self.emitter.emit(self.cur_token.value + " = ")
            self.match(TokenKind.IDENT)
            self.match(TokenKind.EQUAL)

            if self.check_token(TokenKind.STRING):
                # self.emitter.emit_line(f"\"{self.cur_token.value}\"")
                self.advance()
                while self.check_token(TokenKind.PLUS):
                    # self.emitter.emit_line(" + ")

                    self.advance()
                    if self.check_token(TokenKind.STRING):
                        # self.emitter.emit_line(f"\"{self.cur_token.value}\"")
                        self.advance()
                    elif self.check_token(TokenKind.IDENT):
                        # self.emitter.emit(self.cur_token.value)
                        self.advance()
                    elif self.check_token(TokenKind.NUMBER):
                        # self.emitter.emit(self.cur_token.value)
                        self.advance()
                    else:
                        self.abort("Expected string, number or an identifier")
            else:
                self.expression()
            # self.emitter.emit_line(";")
            # ----
        
        elif self.check_token(TokenKind.VAR):
            """
            Variable Declaration

            Syntax:
                1.  var IDENTIFIER = EXPRESSION
            """
            if self.dev:
                print("Var-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
                # self.emitter.add_header(f"auto {self.cur_token.value};")

            # self.emitter.emit(f"{self.cur_token.value} = ")
            self.match(TokenKind.IDENT)
            self.match(TokenKind.EQUAL)

            if self.check_token(TokenKind.STRING):
                # self.emitter.emit_line(f"\"{self.cur_token.value}\"")
                self.advance()
                while self.check_token(TokenKind.PLUS):
                    # self.emitter.emit_line(" + ")

                    self.advance()
                    if self.check_token(TokenKind.STRING):
                        # self.emitter.emit_line(f"\"{self.cur_token.value}\"")
                        self.advance()
                    elif self.check_token(TokenKind.IDENT):
                        # self.emitter.emit(self.cur_token.value)
                        self.advance()
                    elif self.check_token(TokenKind.NUMBER):
                        # self.emitter.emit(self.cur_token.value)
                        self.advance()
                    else:
                        self.abort("Expected string, number or an identifier")
            else:
                self.expression()
            # self.emitter.emit_line(";")
            # ----

        elif self.check_token(TokenKind.INPUT):
            """
            Input Statement

            Syntax:
                1.  input IDENTIFIER
            """
            if self.dev:
                print("Input-Statement")
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
                # self.emitter.add_header(f"float {self.cur_token.value};")

            # self.emitter.emit_line("if(0 == scanf(\"%" + "f\", &{self.cur_token.value})) {")
            # self.emitter.emit_line(self.cur_token.value + " = 0;")
            # self.emitter.emit("scanf_s(\"%")
            # self.emitter.emit_line("*s\");")
            # self.emitter.emit_line("}")
            self.match(TokenKind.IDENT)
            # ----

        elif self.check_token(TokenKind.IDENT):
            """
            Assignment Statement

            Syntax:
                1.  IDENTIFIER = EXPRESSION
            """
            if self.dev:
                print("Assignment-Statement")

            self.advance()

            if self.cur_token.value not in self.symbols:
                self.abort(f"The name '{self.cur_token.value}' does not exist in the current convalue")
            
            # self.emitter.emit(self.cur_token.value + " = ")
            self.match(TokenKind.EQUAL)

            if self.check_token(TokenKind.STRING):
                # self.emitter.emit_line(f"\"{self.cur_token.value}\"")
                self.advance()
                while self.check_token(TokenKind.PLUS):
                    # self.emitter.emit_line(" + ")

                    self.advance()
                    if self.check_token(TokenKind.STRING):
                        # self.emitter.emit_line(f"\"{self.cur_token.value}\"")
                        self.advance()
                    elif self.check_token(TokenKind.IDENT):
                        # self.emitter.emit(self.cur_token.value)
                        self.advance()
                    elif self.check_token(TokenKind.NUMBER):
                        # self.emitter.emit(self.cur_token.value)
                        self.advance()
                    else:
                        self.abort("Expected string, number or an identifier")
            else:
                self.expression()
            # self.emitter.emit_line(";")       
        else:
            self.abort(f"Invalid statement at {self.cur_token.kind.name} {self.cur_token.value if self.cur_token.value is not None else ''}")

    def comparison(self):
        """
        Comparison
        
        Syntax:
            1.  EXPRESSION
            2.  EXPRESSION COMPARISON EXPRESSION
            3.  EXPRESSION COMPARISON EXPRESSION...
        """
        if self.dev:
            print("Comparison")
        
        self.expression()
        
        if self.is_comparison_operator():
            # self.emitter.emit(self.cur_token.value)
            self.advance()
            self.expression()

        while self.is_comparison_operator():
            # self.emitter.emit(self.cur_token.value)
            self.advance()
            self.expression()

    def expression(self):
        """
        Expression

        Syntax:
            1.  TERM
            2.  TERM + TERM
            3.  TERM - TERM
        """
        print("Expression")
        self.term()
        while self.check_token(TokenKind.PLUS) or self.check_token(TokenKind.MINUS):
            # self.emitter.emit(self.cur_token.value)
            self.advance()
            self.term()

    def term(self):
        """
        Term

        Syntax:
            1.  FACTOR
            2.  FACTOR * FACTOR
            3.  FACTOR / FACTOR
        """
        if self.dev:
            print("Term")
        
        self.unary()

        while self.check_token(TokenKind.STAR) or self.check_token(TokenKind.SLASH):
            # self.emitter.emit(self.cur_token.value)
            self.advance()
            self.unary()

    def unary(self):
        """
        Unary

        Syntax:
            1.  PLUS FACTOR
            2.  MINUS FACTOR
            3.  NOT FACTOR
            4.  TILDE FACTOR
            5.  PLUSPLUS FACTOR
            6.  MINUSMINUS FACTOR
            7.  FACTOR
        """
        if (
            self.check_token(TokenKind.PLUS) or self.check_token(TokenKind.MINUS) or 
            self.check_token(TokenKind.BANG) or self.check_token(TokenKind.TILDE) or 
            self.check_token(TokenKind.PLUSPLUS) or self.check_token(TokenKind.MINUSMINUS)
        ):
            print(f"Unary ({self.cur_token.value})")
            # self.emitter.emit(self.cur_token.value)
            self.advance()
        self.primary()

    def primary(self):
        """
        Primary

        Syntax:
            1.  NUMBER
            2.  STRING
            3.  IDENTIFIER
            4.  (EXPRESSION)
        """
        if self.check_token(TokenKind.NUMBER):
            print(f"Primary ({self.cur_token.value})")
            # self.emitter.emit(self.cur_token.value)
            self.advance()
        elif self.check_token(TokenKind.IDENT):
            if self.cur_token.value not in self.symbols:
                self.abort(f"Referencing variable before assignment: {self.cur_token.value}")
            
            print(f"Primary ({self.cur_token.value})")
            # self.emitter.emit(self.cur_token.value)
            self.advance()
        else:
            self.abort(f"Unexpected token at {self.cur_token.value}")

    # def skip_new_lines(self):
    #     while self.check_token(TokenKind.NEWLINE):
    #         self.advance()

    # def new_line(self):
    #     # print("NEWLINE")
    #     print("...")
    #     self.match(TokenKind.NEWLINE)
    #     while self.check_token(TokenKind.NEWLINE):
    #         self.advance()