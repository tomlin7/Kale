import sys
from CodeAnalysis.Syntax.syntaxkind import SyntaxKind

import colorama, termcolor
colorama.init()

class Parser:
    def __init__(self, token_list, debug=False):
        self.token_list = token_list
        self.position = -1
        self.debug = debug

        # ----
        self.symbols = set()
        self.labels_declared = set()
        self.labels_gotoed = set()

        # ----
        self.cur_token = None
        
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
                self.check_token(SyntaxKind.GreaterToken) or self.check_token(SyntaxKind.GreaterOrEqualsToken) or
                self.check_token(SyntaxKind.LessToken) or self.check_token(SyntaxKind.LessOrEqualsToken) or
                self.check_token(SyntaxKind.EqualsEqualsToken) or self.check_token(SyntaxKind.BangEqualsToken)
        )

    def abort(self, message):
        """
        Aborts the program with the passed message.
        """
        print(termcolor.colored(f"Error: {message}", "red"))
        sys.exit()

    # Production rules.
    def program(self):
        """
        Program entry point
        """
        if self.debug:
            print("Program")

        while not self.check_token(SyntaxKind.EndOfFileToken):
            self.statement()

        for label in self.labels_gotoed:
            if label not in self.labels_declared:
                self.abort("Attempting to goto to undeclared label: " + label)

    def statement(self):
        """
        Statements Parser
        """

        if self.check_token(SyntaxKind.PrintKeyword):
            """
            Print Statement
            
            Syntax: 
                1.  print(StringKeyword)
                2.  print(EXPRESSION)
            """
            if self.debug:
                print("Print-Statement")

            self.advance()

            # Body
            # ----
            self.match(SyntaxKind.OpenParenthesisToken)
            if self.check_token(SyntaxKind.StringToken):
                self.advance()
            else:
                self.expression()
            self.match(SyntaxKind.CloseParenthesisToken)
        
        elif self.check_token(SyntaxKind.IfKeyword):
            """
            If/If-else Statement
            
            Syntax: 
                1.  if(EXPRESSION) 
                    { 
                        STATEMENTS 
                    }
                    
                2.  if (COMPARISON) 
                    {
                        STATEMENTS
                    } else {
                        STATEMENTS        
                    }
                3.  if (COMPARISON)
                    {
                        STATEMENTS
                    } else if (COMPARISON)
                    {
                        STATEMENTS
                    } else {
                        STATEMENTS
                    }
            """
            if self.debug:
                print("If-Statement")

            self.advance()

            # Comparison
            # ----
            self.match(SyntaxKind.OpenParenthesisToken)
            self.comparison()
            self.match(SyntaxKind.CloseParenthesisToken)

            # Body
            # ----
            self.match(SyntaxKind.OpenBraceToken)
            while not self.check_token(SyntaxKind.CloseBraceToken):
                self.statement()

            self.match(SyntaxKind.CloseBraceToken)

            # Extensions
            # ----
            while self.check_token(SyntaxKind.ElseKeyword):
                self.advance()

                if self.check_token(SyntaxKind.IfKeyword):
                    if self.debug:
                        print("Else-If-Statement")
                    
                    self.advance()

                    # Comparison
                    # ----
                    self.match(SyntaxKind.OpenParenthesisToken)
                    self.comparison()
                    self.match(SyntaxKind.CloseParenthesisToken)
                    
                    # Body
                    # ----
                    self.match(SyntaxKind.OpenBraceToken)
                    while not self.check_token(SyntaxKind.CloseBraceToken):
                        self.statement()

                    self.match(SyntaxKind.CloseBraceToken)

                elif self.check_token(SyntaxKind.OpenBraceToken):
                    if self.debug:
                        print("Else-Statement")
                    
                    self.advance()
                    
                    # Body
                    # ----
                    while not self.check_token(SyntaxKind.CloseBraceToken):
                        self.statement()

                    self.match(SyntaxKind.CloseBraceToken)
                    
                    break

        elif self.check_token(SyntaxKind.WhileKeyword):
            """
            While Statement

            Syntax:
                1.  while(EXPRESSION)
                    {
                        STATEMENTS
                    }
            """
            if self.debug:
                print("While-Statement")
            
            self.advance()

            # Comparison
            # ----
            self.match(SyntaxKind.OpenParenthesisToken)
            self.comparison()
            self.match(SyntaxKind.CloseParenthesisToken)

            # Body
            # ----
            self.match(SyntaxKind.OpenBraceToken)
            while not self.check_token(SyntaxKind.CloseBraceToken):
                self.statement()
            
            self.match(SyntaxKind.CloseBraceToken)
        
        elif self.check_token(SyntaxKind.ForKeyword):
            """
            For Statement

            Syntax:
                1.  for(INITIALIZATION; CONDITION; INCREMENT)
                    {
                        STATEMENTS
                    }
            """
            if self.debug:
                print("For-Statement")
            
            self.advance()

            # Initialization, Condition, Increment
            # ----
            self.match(SyntaxKind.OpenParenthesisToken)
            self.statement()
            self.match(SyntaxKind.SemiToken)
            self.comparison()
            self.match(SyntaxKind.SemiToken)
            self.expression()
            self.match(SyntaxKind.CloseParenthesisToken)

            # Body
            # ----
            self.match(SyntaxKind.OpenBraceToken)
            while not self.check_token(SyntaxKind.CloseBraceToken):
                self.statement()
            
            self.match(SyntaxKind.CloseBraceToken)

        elif self.check_token(SyntaxKind.LabelKeyword):
            """
            Label Statement

            Syntax:
                1.  label IDENTIFIER:
            """
            if self.debug:
                print("Label-Statement")

            self.advance()

            # ----
            if self.cur_token.value in self.labels_declared:
                self.abort(f"Label already exists: {self.cur_token.value}")
            self.labels_declared.add(self.cur_token.value)

            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.ColonToken)

        elif self.check_token(SyntaxKind.GotoKeyword):
            """
            Goto Statement

            Syntax:
                1.  goto IDENTIFIER
            """
            if self.debug:
                print("Goto-Statement")
    
            self.advance()
            
            # ----
            self.labels_gotoed.add(self.cur_token.value)
            
            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
        
        elif self.check_token(SyntaxKind.IntKeyword):
            """
            Integer Declaration

            Syntax:
                1.  int IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Int-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
            
            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.EqualsToken)
            self.expression()

        elif self.check_token(SyntaxKind.CharKeyword):
            """
            Char Declaration

            Syntax:
                1.  char IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Char-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
            
            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.EqualsToken)
            self.expression()

        elif self.check_token(SyntaxKind.FloatKeyword):
            """
            Float Declaration

            Syntax:
                1.  float IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Float-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
            
            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.EqualsToken)
            self.expression()
        
        
        
        elif self.check_token(SyntaxKind.BoolKeyword):
            """
            Boolean Declaration

            Syntax:
                1.  bool IDENTIFIER = true
                2.  bool IDENTIFIER = false
                3.  bool IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Bool-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
            
            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            
            self.match(SyntaxKind.EqualsToken)
            if self.check_token(SyntaxKind.TrueKeyword):
                self.match(SyntaxKind.TrueKeyword)
            elif self.check_token(SyntaxKind.FalseKeyword):
                self.match(SyntaxKind.FalseKeyword)
            else:
                self.expression()

        elif self.check_token(SyntaxKind.LetKeyword):
            """
            Let Statement

            Syntax:
                1.  let IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Let-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
            else:
                self.abort(f"A local variable named '{self.cur_token.value}' is already defined in this scope")

            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.EqualsToken)
            self.expression()
        
        elif self.check_token(SyntaxKind.VarKeyword):
            """
            Variable Declaration

            Syntax:
                1.  var IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Var-Statement")
            
            self.advance()

            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)

            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.EqualsToken)
            self.expression()

        elif self.check_token(SyntaxKind.InputKeyword):
            """
            Input Statement

            Syntax:
                1.  input IDENTIFIER
            """
            if self.debug:
                print("Input-Statement")
            
            self.advance()

            # Body
            # ----
            if self.cur_token.value not in self.symbols:
                self.symbols.add(self.cur_token.value)
            self.match(SyntaxKind.IdentifierToken)

        elif self.check_token(SyntaxKind.IdentifierToken):
            """
            Assignment Statement

            Syntax:
                1.  IDENTIFIER = EXPRESSION
            """
            if self.debug:
                print("Assignment-Statement")

            # ----
            if self.cur_token.value not in self.symbols:
                self.abort(f"The name '{self.cur_token.value}' does not exist in the current convalue")
            
            # Body
            # ----
            self.match(SyntaxKind.IdentifierToken)
            self.match(SyntaxKind.EqualsToken)
            self.expression()
            
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
        if self.debug:
            print("Comparison")
        
        self.expression()
        
        if self.is_comparison_operator():
            self.advance()
            self.expression()

        while self.is_comparison_operator():
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
        while self.check_token(SyntaxKind.PlusToken) or self.check_token(SyntaxKind.MinusToken):
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
        if self.debug:
            print("Term")
        
        self.unary()

        while self.check_token(SyntaxKind.StartToken) or self.check_token(SyntaxKind.SlashToken):
            self.advance()
            self.unary()

    def unary(self):
        """
        Unary

        Syntax:
            1.  PlusToken FACTOR
            2.  MinusToken FACTOR
            3.  NOT FACTOR
            4.  TildeToken FACTOR
            5.  PlusPlusToken FACTOR
            6.  MinusMinusToken FACTOR
            7.  FACTOR
        """
        # Prefix
        if (self.check_token(SyntaxKind.PlusToken) or self.check_token(SyntaxKind.MinusToken) or
            self.check_token(SyntaxKind.BangToken) or self.check_token(SyntaxKind.TildeToken) or
            self.check_token(SyntaxKind.PlusPlusToken) or self.check_token(SyntaxKind.MinusMinusToken)):
            print(f"Unary ({self.cur_token.value})")
            self.advance()
        
        self.primary()
        
        # Postfix
        if (self.check_token(SyntaxKind.PlusPlusToken) or self.check_token(SyntaxKind.MinusMinusToken)):
            print(f"Unary ({self.cur_token.value})")
            self.advance()

    def primary(self):
        """
        Primary

        Syntax:
            1.  NUMBER
            2.  StringKeyword
            3.  IDENTIFIER
            4.  (EXPRESSION)
        """
        if self.check_token(SyntaxKind.NumberToken) or self.check_token(SyntaxKind.StringToken):
            print(f"Primary ({self.cur_token.value})")
            self.advance()
        
        elif self.check_token(SyntaxKind.IdentifierToken):
            if self.cur_token.value not in self.symbols:
                self.abort(f"Referencing variable before assignment: {self.cur_token.value}")
            
            print(f"Primary ({self.cur_token.value})")
            self.advance()
        
        elif self.check_token(SyntaxKind.OpenParenthesisToken):
            print("Primary (")
            self.advance()
            self.expression()
            self.match(SyntaxKind.CloseParenthesisToken)
            print(")")
        
        else:
            self.abort(f"Unexpected token {self.cur_token.kind} {f'at {self.cur_token.value}' if self.cur_token.value is not None else ''}")
