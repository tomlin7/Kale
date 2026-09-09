from ..diagnostics.source_text import SourceText
from ..diagnostics.diagnostic_bag import DiagnosticBag
from ..syntax.syntax_kind import SyntaxKind
from ..syntax.syntax_token import SyntaxToken
from ..syntax.syntax_facts import (
    is_type_keyword,
    is_assignment_operator,
    get_unary_operator_precedence,
    get_binary_operator_precedence,
)
from ..syntax.lexer import Lexer
from ..ast.nodes import (
    Expression,
    LiteralExpression,
    VariableExpression,
    GroupingExpression,
    UnaryExpression,
    BinaryExpression,
    AssignmentExpression,
    CallExpression,
    Statement,
    BlockStatement,
    ParameterNode,
    FunctionDeclarationStatement,
    VariableDeclarationStatement,
    ExpressionStatement,
    IfStatement,
    ElseClause,
    WhileStatement,
    ForStatement,
    PrintStatement,
    ReturnStatement,
    BreakStatement,
    ContinueStatement,
    CompilationUnit,
)

class Parser:
    """Parses a stream of syntax tokens into an Abstract Syntax Tree (AST)."""
    def __init__(self, source_text: SourceText, diagnostics: DiagnosticBag | None = None):
        self.source_text = source_text
        self.diagnostics = diagnostics if diagnostics is not None else DiagnosticBag()
        lexer = Lexer(source_text, self.diagnostics)
        self.tokens = lexer.lex_all(include_trivia=False)
        self._position = 0

    @property
    def _cur_token(self) -> SyntaxToken:
        return self._peek(0)

    def _peek(self, offset: int = 0) -> SyntaxToken:
        idx = self._position + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def _check(self, kind: SyntaxKind) -> bool:
        return self._cur_token.kind == kind

    def _advance(self) -> SyntaxToken:
        tok = self._cur_token
        if self._cur_token.kind != SyntaxKind.EndOfFileToken:
            self._position += 1
        return tok

    def _match(self, kind: SyntaxKind) -> SyntaxToken:
        if self._cur_token.kind == kind:
            return self._advance()
        self.diagnostics.report_unexpected_token(self._cur_token.span, self._cur_token.kind.name, kind.name)
        return SyntaxToken(kind, self._cur_token.span, None, "")

    def _synchronize(self):
        """Advances until the next likely statement boundary to recover from errors."""
        self._advance()
        while self._cur_token.kind != SyntaxKind.EndOfFileToken:
            if self._peek(-1).kind == SyntaxKind.SemicolonToken or self._peek(-1).kind == SyntaxKind.CloseBraceToken:
                return
            if self._cur_token.kind in (
                SyntaxKind.IfKeyword,
                SyntaxKind.WhileKeyword,
                SyntaxKind.ForKeyword,
                SyntaxKind.PrintKeyword,
                SyntaxKind.ReturnKeyword,
                SyntaxKind.LetKeyword,
                SyntaxKind.VarKeyword,
                SyntaxKind.ConstKeyword,
                SyntaxKind.IntKeyword,
                SyntaxKind.FloatKeyword,
                SyntaxKind.DoubleKeyword,
                SyntaxKind.StringKeyword,
                SyntaxKind.BoolKeyword,
                SyntaxKind.CharKeyword,
            ):
                return
            self._advance()

    def parse_compilation_unit(self) -> CompilationUnit:
        statements: list[Statement] = []
        while self._cur_token.kind != SyntaxKind.EndOfFileToken:
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        eof_token = self._match(SyntaxKind.EndOfFileToken)
        return CompilationUnit(statements=statements, end_of_file_token=eof_token)

    def parse_statement(self) -> Statement | None:
        try:
            if self._check(SyntaxKind.OpenBraceToken):
                return self.parse_block_statement()
            if self._is_function_declaration_start():
                return self.parse_function_declaration()
            if self._is_declaration_start():
                return self.parse_variable_declaration()
            if self._check(SyntaxKind.IfKeyword):
                return self.parse_if_statement()
            if self._check(SyntaxKind.WhileKeyword):
                return self.parse_while_statement()
            if self._check(SyntaxKind.ForKeyword):
                return self.parse_for_statement()
            if self._check(SyntaxKind.PrintKeyword):
                return self.parse_print_statement()
            if self._check(SyntaxKind.ReturnKeyword):
                return self.parse_return_statement()
            if self._check(SyntaxKind.BreakKeyword):
                return self.parse_break_statement()
            if self._check(SyntaxKind.ContinueKeyword):
                return self.parse_continue_statement()
            return self.parse_expression_statement()
        except Exception:
            self._synchronize()
            return None

    def _is_function_declaration_start(self) -> bool:
        k = self._cur_token.kind
        return (
            (is_type_keyword(k) or k in (SyntaxKind.LetKeyword, SyntaxKind.VarKeyword))
            and self._peek(1).kind == SyntaxKind.IdentifierToken
            and self._peek(2).kind == SyntaxKind.OpenParenthesisToken
        )

    def _is_declaration_start(self) -> bool:
        k = self._cur_token.kind
        return is_type_keyword(k) or k in (SyntaxKind.LetKeyword, SyntaxKind.VarKeyword, SyntaxKind.ConstKeyword)

    def parse_function_declaration(self) -> FunctionDeclarationStatement:
        return_type_token = self._advance()
        identifier_token = self._match(SyntaxKind.IdentifierToken)
        open_paren = self._match(SyntaxKind.OpenParenthesisToken)

        parameters: list[ParameterNode] = []
        if not self._check(SyntaxKind.CloseParenthesisToken):
            param_type = self._advance()
            param_name = self._match(SyntaxKind.IdentifierToken)
            parameters.append(ParameterNode(param_type, param_name))

            while self._check(SyntaxKind.CommaToken):
                self._advance()
                param_type = self._advance()
                param_name = self._match(SyntaxKind.IdentifierToken)
                parameters.append(ParameterNode(param_type, param_name))

        close_paren = self._match(SyntaxKind.CloseParenthesisToken)
        body = self.parse_block_statement()
        return FunctionDeclarationStatement(
            return_type_token,
            identifier_token,
            open_paren,
            parameters,
            close_paren,
            body,
        )

    def parse_block_statement(self) -> BlockStatement:
        open_brace = self._match(SyntaxKind.OpenBraceToken)
        statements: list[Statement] = []
        while not self._check(SyntaxKind.CloseBraceToken) and not self._check(SyntaxKind.EndOfFileToken):
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        close_brace = self._match(SyntaxKind.CloseBraceToken)
        return BlockStatement(open_brace, statements, close_brace)

    def parse_variable_declaration(self) -> VariableDeclarationStatement:
        type_token = self._advance() # int, double, let, var, etc.
        identifier = self._match(SyntaxKind.IdentifierToken)

        equals_token = None
        initializer = None
        if self._check(SyntaxKind.EqualsToken):
            equals_token = self._advance()
            initializer = self.parse_expression()

        semi = None
        if self._check(SyntaxKind.SemicolonToken):
            semi = self._advance()
        return VariableDeclarationStatement(type_token, identifier, equals_token, initializer, semi)

    def parse_if_statement(self) -> IfStatement:
        if_kw = self._match(SyntaxKind.IfKeyword)
        open_p = self._match(SyntaxKind.OpenParenthesisToken)
        cond = self.parse_expression()
        close_p = self._match(SyntaxKind.CloseParenthesisToken)
        then_stmt = self.parse_statement() or BlockStatement(open_p, [], close_p)

        else_clause = None
        if self._check(SyntaxKind.ElseKeyword):
            else_kw = self._advance()
            else_stmt = self.parse_statement() or BlockStatement(open_p, [], close_p)
            else_clause = ElseClause(else_kw, else_stmt)

        return IfStatement(if_kw, open_p, cond, close_p, then_stmt, else_clause)

    def parse_while_statement(self) -> WhileStatement:
        while_kw = self._match(SyntaxKind.WhileKeyword)
        open_p = self._match(SyntaxKind.OpenParenthesisToken)
        cond = self.parse_expression()
        close_p = self._match(SyntaxKind.CloseParenthesisToken)
        body = self.parse_statement() or BlockStatement(open_p, [], close_p)
        return WhileStatement(while_kw, open_p, cond, close_p, body)

    def parse_for_statement(self) -> ForStatement:
        for_kw = self._match(SyntaxKind.ForKeyword)
        open_p = self._match(SyntaxKind.OpenParenthesisToken)

        init = None
        if not self._check(SyntaxKind.SemicolonToken):
            if self._is_declaration_start():
                init = self.parse_variable_declaration()
            else:
                init = self.parse_expression_statement()
        else:
            self._advance() # consume ';'

        cond = None
        if not self._check(SyntaxKind.SemicolonToken):
            cond = self.parse_expression()
        second_semi = self._match(SyntaxKind.SemicolonToken)

        inc = None
        if not self._check(SyntaxKind.CloseParenthesisToken):
            inc = self.parse_expression()
        close_p = self._match(SyntaxKind.CloseParenthesisToken)

        body = self.parse_statement() or BlockStatement(open_p, [], close_p)
        return ForStatement(for_kw, open_p, init, cond, second_semi, inc, close_p, body)

    def parse_print_statement(self) -> PrintStatement:
        print_kw = self._match(SyntaxKind.PrintKeyword)
        open_p = self._match(SyntaxKind.OpenParenthesisToken)
        args: list[Expression] = []
        if not self._check(SyntaxKind.CloseParenthesisToken):
            args.append(self.parse_expression())
            while self._check(SyntaxKind.CommaToken):
                self._advance()
                args.append(self.parse_expression())
        close_p = self._match(SyntaxKind.CloseParenthesisToken)
        semi = self._match(SyntaxKind.SemicolonToken) if self._check(SyntaxKind.SemicolonToken) else None
        return PrintStatement(print_kw, open_p, args, close_p, semi)

    def parse_return_statement(self) -> ReturnStatement:
        ret_kw = self._match(SyntaxKind.ReturnKeyword)
        expr = None
        if not self._check(SyntaxKind.SemicolonToken) and not self._check(SyntaxKind.CloseBraceToken):
            expr = self.parse_expression()
        semi = self._match(SyntaxKind.SemicolonToken) if self._check(SyntaxKind.SemicolonToken) else None
        return ReturnStatement(ret_kw, expr, semi)

    def parse_break_statement(self) -> BreakStatement:
        kw = self._match(SyntaxKind.BreakKeyword)
        semi = self._match(SyntaxKind.SemicolonToken) if self._check(SyntaxKind.SemicolonToken) else None
        return BreakStatement(kw, semi)

    def parse_continue_statement(self) -> ContinueStatement:
        kw = self._match(SyntaxKind.ContinueKeyword)
        semi = self._match(SyntaxKind.SemicolonToken) if self._check(SyntaxKind.SemicolonToken) else None
        return ContinueStatement(kw, semi)

    def parse_expression_statement(self) -> ExpressionStatement:
        expr = self.parse_expression()
        semi = self._match(SyntaxKind.SemicolonToken) if self._check(SyntaxKind.SemicolonToken) else None
        return ExpressionStatement(expr, semi)

    # ==========================================
    # Pratt Parsing for Expressions
    # ==========================================

    def parse_expression(self, parent_precedence: int = 0) -> Expression:
        unary_prec = get_unary_operator_precedence(self._cur_token.kind)
        if unary_prec != 0 and unary_prec >= parent_precedence:
            op_token = self._advance()
            operand = self.parse_expression(unary_prec)
            left = UnaryExpression(op_token, operand, is_postfix=False)
        else:
            left = self._parse_primary_expression()

        # Postfix ++ and --
        if self._cur_token.kind in (SyntaxKind.PlusPlusToken, SyntaxKind.MinusMinusToken):
            postfix_op = self._advance()
            left = UnaryExpression(postfix_op, left, is_postfix=True)

        # Infix / Assignment
        while True:
            # Check for assignment
            if is_assignment_operator(self._cur_token.kind):
                op_token = self._advance()
                if not isinstance(left, VariableExpression):
                    self.diagnostics.report(left.span, "The left-hand side of an assignment must be a variable.")
                    right = self.parse_expression(0)
                    return left
                right = self.parse_expression(0) # Right-associative
                left = AssignmentExpression(left.identifier_token, op_token, right)
                continue

            prec = get_binary_operator_precedence(self._cur_token.kind)
            if prec == 0 or prec <= parent_precedence:
                break

            op_token = self._advance()
            # DoubleStar (exponentiation) is right-associative
            next_prec = prec - 1 if op_token.kind == SyntaxKind.DoubleStarToken else prec
            right = self.parse_expression(next_prec)
            left = BinaryExpression(left, op_token, right)

        return left

    def _parse_primary_expression(self) -> Expression:
        cur = self._cur_token

        # Literals
        if cur.kind == SyntaxKind.NumberToken:
            tok = self._advance()
            return LiteralExpression(tok, tok.value)

        if cur.kind == SyntaxKind.StringToken:
            tok = self._advance()
            return LiteralExpression(tok, tok.value)

        if cur.kind in (SyntaxKind.TrueKeyword, SyntaxKind.FalseKeyword):
            tok = self._advance()
            return LiteralExpression(tok, tok.value)

        if cur.kind == SyntaxKind.NullKeyword:
            tok = self._advance()
            return LiteralExpression(tok, None)

        # Parenthesized expression
        if cur.kind == SyntaxKind.OpenParenthesisToken:
            open_p = self._advance()
            expr = self.parse_expression()
            close_p = self._match(SyntaxKind.CloseParenthesisToken)
            return GroupingExpression(open_p, expr, close_p)

        # Identifier or Call expression
        if cur.kind == SyntaxKind.IdentifierToken:
            ident = self._advance()
            if self._check(SyntaxKind.OpenParenthesisToken):
                open_p = self._advance()
                args: list[Expression] = []
                if not self._check(SyntaxKind.CloseParenthesisToken):
                    args.append(self.parse_expression())
                    while self._check(SyntaxKind.CommaToken):
                        self._advance()
                        args.append(self.parse_expression())
                close_p = self._match(SyntaxKind.CloseParenthesisToken)
                return CallExpression(ident, open_p, args, close_p)
            return VariableExpression(ident)

        # Fallback error recovery token
        self.diagnostics.report_unexpected_token(cur.span, cur.kind.name, "expression")
        tok = self._advance()
        return LiteralExpression(tok, None)
