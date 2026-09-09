from ..diagnostics.source_text import SourceText
from ..diagnostics.diagnostic_bag import DiagnosticBag
from ..diagnostics.text_span import TextSpan
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
    CastExpression,
    UnaryExpression,
    BinaryExpression,
    AssignmentExpression,
    DereferenceAssignmentExpression,
    CallExpression,
    ArrayLiteralExpression,
    IndexExpression,
    IndexAssignmentExpression,
    MemberAccessExpression,
    MemberAssignmentExpression,
    ArrowAccessExpression,
    ArrowAssignmentExpression,
    AllocExpression,
    Statement,
    BlockStatement,
    ParameterNode,
    StructFieldNode,
    StructDeclarationStatement,
    FunctionDeclarationStatement,
    VariableDeclarationStatement,
    ExpressionStatement,
    IfStatement,
    ElseClause,
    WhileStatement,
    ForStatement,
    PrintStatement,
    FreeStatement,
    ReturnStatement,
    BreakStatement,
    ContinueStatement,
    ImportStatement,
    FromImportStatement,
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
            if self._check(SyntaxKind.ImportKeyword):
                return self.parse_import_statement()
            if self._check(SyntaxKind.FromKeyword):
                return self.parse_from_import_statement()
            if self._check(SyntaxKind.StructKeyword):
                return self.parse_struct_declaration()
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
            if self._check(SyntaxKind.FreeKeyword):
                return self.parse_free_statement()
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
        if not (is_type_keyword(k) or k in (SyntaxKind.LetKeyword, SyntaxKind.VarKeyword) or k == SyntaxKind.IdentifierToken):
            return False
        idx = 1
        # Advance through any dot qualifier e.g. geo.Point
        if self._peek(idx).kind == SyntaxKind.DotToken and self._peek(idx + 1).kind == SyntaxKind.IdentifierToken:
            idx += 2
        # Advance through any '*' or '[...]' to check if ident followed by '('
        while True:
            if self._peek(idx).kind == SyntaxKind.StarToken:
                idx += 1
            elif self._peek(idx).kind == SyntaxKind.OpenBracketToken:
                idx += 1
                if self._peek(idx).kind == SyntaxKind.NumberToken:
                    idx += 1
                if self._peek(idx).kind == SyntaxKind.CloseBracketToken:
                    idx += 1
                else:
                    return False
            else:
                break
        return self._peek(idx).kind == SyntaxKind.IdentifierToken and self._peek(idx + 1).kind == SyntaxKind.OpenParenthesisToken

    def _is_declaration_start(self) -> bool:
        k = self._cur_token.kind
        if is_type_keyword(k) or k in (SyntaxKind.LetKeyword, SyntaxKind.VarKeyword, SyntaxKind.ConstKeyword):
            return True
        # Check if user-defined struct identifier as type: `Point p;`, `geo.Point p;`, `Point* p;`, or `Point[3] points;`
        if k == SyntaxKind.IdentifierToken:
            idx = 1
            if self._peek(idx).kind == SyntaxKind.DotToken and self._peek(idx + 1).kind == SyntaxKind.IdentifierToken:
                idx += 2
            while True:
                if self._peek(idx).kind == SyntaxKind.StarToken:
                    idx += 1
                elif self._peek(idx).kind == SyntaxKind.OpenBracketToken:
                    idx += 1
                    if self._peek(idx).kind == SyntaxKind.NumberToken:
                        idx += 1
                    if self._peek(idx).kind == SyntaxKind.CloseBracketToken:
                        idx += 1
                    else:
                        break
                else:
                    break
            if self._peek(idx).kind == SyntaxKind.IdentifierToken:
                return True
        return False

    def _is_cast_expression_start(self) -> bool:
        """Checks if current token is '(' followed by a valid type and ')'."""
        if self._cur_token.kind != SyntaxKind.OpenParenthesisToken:
            return False
        k = self._peek(1).kind
        idx = 1
        if is_type_keyword(k):
            idx = 2
        elif k == SyntaxKind.IdentifierToken:
            idx = 2
            if self._peek(idx).kind == SyntaxKind.DotToken and self._peek(idx + 1).kind == SyntaxKind.IdentifierToken:
                idx += 2
        else:
            return False

        # Scan any pointer stars or array brackets
        while True:
            if self._peek(idx).kind == SyntaxKind.StarToken:
                idx += 1
            elif self._peek(idx).kind == SyntaxKind.OpenBracketToken:
                idx += 1
                if self._peek(idx).kind == SyntaxKind.NumberToken:
                    idx += 1
                if self._peek(idx).kind == SyntaxKind.CloseBracketToken:
                    idx += 1
                else:
                    return False
            else:
                break

        return self._peek(idx).kind == SyntaxKind.CloseParenthesisToken

    def parse_import_statement(self) -> ImportStatement:
        import_kw = self._match(SyntaxKind.ImportKeyword)
        module_path = self._match(SyntaxKind.StringToken)
        as_kw = None
        alias_tok = None
        if self._check(SyntaxKind.AsKeyword):
            as_kw = self._advance()
            alias_tok = self._match(SyntaxKind.IdentifierToken)
        semi = None
        if self._check(SyntaxKind.SemicolonToken):
            semi = self._advance()
        return ImportStatement(import_kw, module_path, as_kw, alias_tok, semi)

    def parse_from_import_statement(self) -> FromImportStatement:
        from_kw = self._match(SyntaxKind.FromKeyword)
        module_path = self._match(SyntaxKind.StringToken)
        import_kw = self._match(SyntaxKind.ImportKeyword)
        symbols: list[SyntaxToken] = []
        sym = self._match(SyntaxKind.IdentifierToken)
        symbols.append(sym)
        while self._check(SyntaxKind.CommaToken):
            self._advance()
            sym = self._match(SyntaxKind.IdentifierToken)
            symbols.append(sym)
        semi = None
        if self._check(SyntaxKind.SemicolonToken):
            semi = self._advance()
        return FromImportStatement(from_kw, module_path, import_kw, symbols, semi)

    def parse_struct_declaration(self) -> StructDeclarationStatement:
        struct_kw = self._match(SyntaxKind.StructKeyword)
        name_tok = self._match(SyntaxKind.IdentifierToken)
        open_brace = self._match(SyntaxKind.OpenBraceToken)
        fields: list[StructFieldNode] = []
        while not self._check(SyntaxKind.CloseBraceToken) and not self._check(SyntaxKind.EndOfFileToken):
            f_type = self.parse_type_token()
            f_name = self._match(SyntaxKind.IdentifierToken)
            f_semi = self._match(SyntaxKind.SemicolonToken)
            fields.append(StructFieldNode(f_type, f_name, f_semi))
        close_brace = self._match(SyntaxKind.CloseBraceToken)
        # Optional trailing semicolon on struct declaration `struct Foo { ... };`
        if self._check(SyntaxKind.SemicolonToken):
            self._advance()
        return StructDeclarationStatement(struct_kw, name_tok, open_brace, fields, close_brace)

    def parse_type_token(self) -> SyntaxToken:
        """Parses a type token, which may be a primitive (e.g. 'int'), pointer ('int*', 'Point**'), or array ('int[]', 'int[5]')."""
        base_type_token = self._advance()
        comp_text = base_type_token.text

        # Support qualified module types: e.g. geo.Point or math.Complex
        if self._check(SyntaxKind.DotToken) and self._peek(1).kind == SyntaxKind.IdentifierToken:
            dot_tok = self._advance()
            member_tok = self._advance()
            comp_text = f"{comp_text}.{member_tok.text}"
            full_span = TextSpan.from_bounds(base_type_token.span.start, member_tok.span.end)
            base_type_token = SyntaxToken(SyntaxKind.IdentifierToken, full_span, value=comp_text, text=comp_text)

        # Handle pointer suffixes (int*, int**, Point*) and array brackets in sequence
        while True:
            if self._check(SyntaxKind.StarToken):
                star_tok = self._advance()
                comp_text = f"{comp_text}*"
                full_span = TextSpan.from_bounds(base_type_token.span.start, star_tok.span.end)
                base_type_token = SyntaxToken(base_type_token.kind, full_span, value=comp_text, text=comp_text)
            elif self._check(SyntaxKind.OpenBracketToken):
                open_b = self._advance()
                sz_str = ""
                if self._check(SyntaxKind.NumberToken):
                    num_tok = self._advance()
                    sz_str = str(num_tok.value)
                close_b = self._match(SyntaxKind.CloseBracketToken)
                full_span = TextSpan.from_bounds(base_type_token.span.start, close_b.span.end)
                comp_text = f"{comp_text}[{sz_str}]"
                base_type_token = SyntaxToken(base_type_token.kind, full_span, value=comp_text, text=comp_text)
            else:
                break

        return base_type_token

    def parse_function_declaration(self) -> FunctionDeclarationStatement:
        return_type_token = self.parse_type_token()
        identifier_token = self._match(SyntaxKind.IdentifierToken)
        open_paren = self._match(SyntaxKind.OpenParenthesisToken)

        parameters: list[ParameterNode] = []
        if not self._check(SyntaxKind.CloseParenthesisToken):
            param_type = self.parse_type_token()
            param_name = self._match(SyntaxKind.IdentifierToken)
            parameters.append(ParameterNode(param_type, param_name))

            while self._check(SyntaxKind.CommaToken):
                self._advance()
                param_type = self.parse_type_token()
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
        type_token = self.parse_type_token() # int, int[], double, let, var, etc.
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

    def parse_free_statement(self) -> FreeStatement:
        free_kw = self._match(SyntaxKind.FreeKeyword)
        open_p = self._match(SyntaxKind.OpenParenthesisToken)
        expr = self.parse_expression(0)
        close_p = self._match(SyntaxKind.CloseParenthesisToken)
        semi = self._match(SyntaxKind.SemicolonToken) if self._check(SyntaxKind.SemicolonToken) else None
        return FreeStatement(free_kw, open_p, expr, close_p, semi)

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
            # Standard unary operand takes unary precedence (7)
            operand = self.parse_expression(unary_prec)
            left = UnaryExpression(op_token, operand, is_postfix=False)
        else:
            left = self._parse_primary_expression()

        # Postfix ++ and --, array indexing [index], member access .member, arrow access ->member, and postfix dereference ^
        while True:
            if self._cur_token.kind in (SyntaxKind.PlusPlusToken, SyntaxKind.MinusMinusToken):
                postfix_op = self._advance()
                left = UnaryExpression(postfix_op, left, is_postfix=True)
            elif self._cur_token.kind == SyntaxKind.CaretToken:
                # If followed by a token that starts an expression, it's binary XOR: a ^ b
                # Postfix deref only applies if next token cannot start an expression or is '.'/'->'/')'/';'/','/'='
                k_next = self._peek(1).kind
                can_start_expr = (
                    k_next in (SyntaxKind.NumberToken, SyntaxKind.StringToken, SyntaxKind.IdentifierToken,
                               SyntaxKind.TrueKeyword, SyntaxKind.FalseKeyword, SyntaxKind.NullKeyword,
                               SyntaxKind.OpenParenthesisToken, SyntaxKind.OpenBracketToken, SyntaxKind.AllocKeyword)
                    or get_unary_operator_precedence(k_next) > 0
                )
                if can_start_expr:
                    # It's binary bitwise XOR (infix), break to let binary operator loop handle it!
                    break
                caret_tok = self._advance()
                left = UnaryExpression(caret_tok, left, is_postfix=True)
            elif self._cur_token.kind == SyntaxKind.OpenBracketToken:
                open_b = self._advance()
                index_expr = self.parse_expression(0)
                close_b = self._match(SyntaxKind.CloseBracketToken)
                left = IndexExpression(left, open_b, index_expr, close_b)
            elif self._cur_token.kind == SyntaxKind.DotToken:
                dot_tok = self._advance()
                member_tok = self._match(SyntaxKind.IdentifierToken)
                left = MemberAccessExpression(left, dot_tok, member_tok)
            elif self._cur_token.kind == SyntaxKind.ArrowToken:
                arrow_tok = self._advance()
                member_tok = self._match(SyntaxKind.IdentifierToken)
                left = ArrowAccessExpression(left, arrow_tok, member_tok)
            elif self._cur_token.kind == SyntaxKind.OpenParenthesisToken:
                open_p = self._advance()
                args: list[Expression] = []
                if not self._check(SyntaxKind.CloseParenthesisToken):
                    args.append(self.parse_expression(0))
                    while self._check(SyntaxKind.CommaToken):
                        self._advance()
                        args.append(self.parse_expression(0))
                close_p = self._match(SyntaxKind.CloseParenthesisToken)
                left = CallExpression(left, open_p, args, close_p)
            elif self._cur_token.kind == SyntaxKind.AsKeyword:
                as_tok = self._advance()
                target_type_tok = self.parse_type_token()
                left = CastExpression(target_type_tok, left, as_token=as_tok)
            else:
                break

        # Infix / Assignment
        while True:
            # Check for assignment (assignments have lowest precedence, parent_precedence must be 0)
            if parent_precedence == 0 and is_assignment_operator(self._cur_token.kind):
                op_token = self._advance()
                if isinstance(left, VariableExpression):
                    right = self.parse_expression(0) # Right-associative
                    left = AssignmentExpression(left.identifier_token, op_token, right)
                    continue
                elif isinstance(left, IndexExpression):
                    right = self.parse_expression(0) # Right-associative
                    left = IndexAssignmentExpression(left.target, left.open_bracket, left.index, left.close_bracket, op_token, right)
                    continue
                elif isinstance(left, MemberAccessExpression):
                    right = self.parse_expression(0) # Right-associative
                    left = MemberAssignmentExpression(left.target, left.dot_token, left.member_token, op_token, right)
                    continue
                elif isinstance(left, ArrowAccessExpression):
                    right = self.parse_expression(0) # Right-associative
                    left = ArrowAssignmentExpression(left.target, left.arrow_token, left.member_token, op_token, right)
                    continue
                elif isinstance(left, UnaryExpression) and (
                    (not left.is_postfix and left.operator_token.kind == SyntaxKind.StarToken)
                    or (left.is_postfix and left.operator_token.kind == SyntaxKind.CaretToken)
                ):
                    right = self.parse_expression(0) # Right-associative
                    left = DereferenceAssignmentExpression(left.operand, op_token, right)
                    continue
                else:
                    self.diagnostics.report(left.span, "The left-hand side of an assignment must be a variable, array index, struct field, or dereference.")
                    right = self.parse_expression(0)
                    return left

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

        # Alloc expression: alloc(Type) or alloc(Type, count)
        if cur.kind == SyntaxKind.AllocKeyword:
            alloc_kw = self._advance()
            open_p = self._match(SyntaxKind.OpenParenthesisToken)
            type_tok = self.parse_type_token()
            count_expr = None
            if self._check(SyntaxKind.CommaToken):
                self._advance()
                count_expr = self.parse_expression(0)
            close_p = self._match(SyntaxKind.CloseParenthesisToken)
            return AllocExpression(alloc_kw, open_p, type_tok, count_expr, close_p)

        # Array literal: [elem1, elem2, ...]
        if cur.kind == SyntaxKind.OpenBracketToken:
            open_b = self._advance()
            elements: list[Expression] = []
            if not self._check(SyntaxKind.CloseBracketToken):
                elements.append(self.parse_expression(0))
                while self._check(SyntaxKind.CommaToken):
                    self._advance()
                    if self._check(SyntaxKind.CloseBracketToken):
                        break
                    elements.append(self.parse_expression(0))
            close_b = self._match(SyntaxKind.CloseBracketToken)
            return ArrayLiteralExpression(open_b, elements, close_b)

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

        # Cast expression: (Type)expr or Parenthesized expression: (expr)
        if cur.kind == SyntaxKind.OpenParenthesisToken:
            if self._is_cast_expression_start():
                open_p = self._advance()
                type_tok = self.parse_type_token()
                close_p = self._match(SyntaxKind.CloseParenthesisToken)
                cast_operand = self.parse_expression(12) # Bind with unary precedence
                return CastExpression(type_tok, cast_operand, open_paren=open_p, close_paren=close_p)

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
