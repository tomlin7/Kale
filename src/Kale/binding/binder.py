from ..diagnostics.diagnostic_bag import DiagnosticBag
from ..syntax.syntax_kind import SyntaxKind
from ..syntax.syntax_token import SyntaxToken
from ..ast.nodes import (
    CompilationUnit,
    Statement,
    BlockStatement,
    VariableDeclarationStatement,
    ExpressionStatement,
    IfStatement,
    WhileStatement,
    ForStatement,
    PrintStatement,
    ReturnStatement,
    BreakStatement,
    ContinueStatement,
    Expression,
    LiteralExpression,
    VariableExpression,
    GroupingExpression,
    UnaryExpression,
    BinaryExpression,
    AssignmentExpression,
    CallExpression,
)
from .types import (
    TypeSymbol,
    TypeInt,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeVoid,
    TypeUnknown,
    lookup_type,
    is_numeric,
    can_convert,
    get_promoted_numeric_type,
)
from .symbols import VariableSymbol, FunctionSymbol
from .scope import Scope
from .bound_nodes import (
    BoundProgram,
    BoundStatement,
    BoundBlockStatement,
    BoundVariableDeclaration,
    BoundExpressionStatement,
    BoundIfStatement,
    BoundWhileStatement,
    BoundForStatement,
    BoundPrintStatement,
    BoundReturnStatement,
    BoundBreakStatement,
    BoundContinueStatement,
    BoundExpression,
    BoundLiteralExpression,
    BoundVariableExpression,
    BoundAssignmentExpression,
    BoundUnaryExpression,
    BoundUnaryOperator,
    BoundBinaryExpression,
    BoundBinaryOperator,
)

class Binder:
    """Walks the AST, resolves symbols, checks types, and produces a typed BoundProgram."""
    def __init__(self, diagnostics: DiagnosticBag):
        self.diagnostics = diagnostics
        self._current_scope = Scope()

    def bind_program(self, compilation_unit: CompilationUnit) -> BoundProgram:
        bound_statements: list[BoundStatement] = []
        for statement in compilation_unit.statements:
            bound_stmt = self.bind_statement(statement)
            if bound_stmt is not None:
                bound_statements.append(bound_stmt)
        return BoundProgram(statements=bound_statements, root_scope=self._current_scope)

    def bind_statement(self, statement: Statement) -> BoundStatement | None:
        if isinstance(statement, BlockStatement):
            return self._bind_block_statement(statement)
        if isinstance(statement, VariableDeclarationStatement):
            return self._bind_variable_declaration(statement)
        if isinstance(statement, IfStatement):
            return self._bind_if_statement(statement)
        if isinstance(statement, WhileStatement):
            return self._bind_while_statement(statement)
        if isinstance(statement, ForStatement):
            return self._bind_for_statement(statement)
        if isinstance(statement, PrintStatement):
            return self._bind_print_statement(statement)
        if isinstance(statement, ReturnStatement):
            return self._bind_return_statement(statement)
        if isinstance(statement, BreakStatement):
            return BoundBreakStatement()
        if isinstance(statement, ContinueStatement):
            return BoundContinueStatement()
        if isinstance(statement, ExpressionStatement):
            return self._bind_expression_statement(statement)
        return None

    def _bind_block_statement(self, statement: BlockStatement) -> BoundBlockStatement:
        self._current_scope = Scope(parent=self._current_scope)
        bound_stmts: list[BoundStatement] = []
        for s in statement.statements:
            b = self.bind_statement(s)
            if b is not None:
                bound_stmts.append(b)
        self._current_scope = self._current_scope.parent # type: ignore
        return BoundBlockStatement(bound_stmts)

    def _bind_variable_declaration(self, statement: VariableDeclarationStatement) -> BoundVariableDeclaration:
        type_token = statement.type_token
        ident = statement.identifier_token
        name = ident.text
        is_const = (type_token.kind == SyntaxKind.ConstKeyword)

        # Bind initializer if present
        bound_init = None
        if statement.initializer is not None:
            bound_init = self.bind_expression(statement.initializer)

        # Determine variable type
        var_type: TypeSymbol = TypeUnknown
        if type_token.kind in (SyntaxKind.LetKeyword, SyntaxKind.VarKeyword, SyntaxKind.ConstKeyword):
            if bound_init is not None:
                var_type = bound_init.type
            else:
                var_type = TypeInt # default type
        else:
            looked_up = lookup_type(type_token.text)
            var_type = looked_up if looked_up is not None else TypeUnknown

        # Check type compatibility
        if bound_init is not None and not can_convert(bound_init.type, var_type):
            self.diagnostics.report_cannot_convert(statement.initializer.span, str(bound_init.type), str(var_type))

        variable = VariableSymbol(name=name, type=var_type, is_read_only=is_const)
        if not self._current_scope.try_declare(variable):
            self.diagnostics.report_variable_already_declared(ident.span, name)

        return BoundVariableDeclaration(variable, bound_init)

    def _bind_if_statement(self, statement: IfStatement) -> BoundIfStatement:
        cond = self.bind_expression(statement.condition)
        if not can_convert(cond.type, TypeBool):
            self.diagnostics.report_cannot_convert(statement.condition.span, str(cond.type), "bool")
        then_stmt = self.bind_statement(statement.then_statement) or BoundBlockStatement([])
        else_stmt = None
        if statement.else_clause is not None:
            else_stmt = self.bind_statement(statement.else_clause.statement)
        return BoundIfStatement(cond, then_stmt, else_stmt)

    def _bind_while_statement(self, statement: WhileStatement) -> BoundWhileStatement:
        cond = self.bind_expression(statement.condition)
        if not can_convert(cond.type, TypeBool):
            self.diagnostics.report_cannot_convert(statement.condition.span, str(cond.type), "bool")
        body = self.bind_statement(statement.body) or BoundBlockStatement([])
        return BoundWhileStatement(cond, body)

    def _bind_for_statement(self, statement: ForStatement) -> BoundForStatement:
        self._current_scope = Scope(parent=self._current_scope)
        init = self.bind_statement(statement.initializer) if statement.initializer else None
        cond = self.bind_expression(statement.condition) if statement.condition else None
        if cond is not None and not can_convert(cond.type, TypeBool):
            self.diagnostics.report_cannot_convert(statement.condition.span, str(cond.type), "bool") # type: ignore
        inc = self.bind_expression(statement.increment) if statement.increment else None
        body = self.bind_statement(statement.body) or BoundBlockStatement([])
        self._current_scope = self._current_scope.parent # type: ignore
        return BoundForStatement(init, cond, inc, body)

    def _bind_print_statement(self, statement: PrintStatement) -> BoundPrintStatement:
        bound_args = [self.bind_expression(arg) for arg in statement.arguments]
        return BoundPrintStatement(bound_args)

    def _bind_return_statement(self, statement: ReturnStatement) -> BoundReturnStatement:
        bound_expr = self.bind_expression(statement.expression) if statement.expression else None
        return BoundReturnStatement(bound_expr)

    def _bind_expression_statement(self, statement: ExpressionStatement) -> BoundExpressionStatement:
        expr = self.bind_expression(statement.expression)
        return BoundExpressionStatement(expr)

    # ==========================================
    # Bind Expressions
    # ==========================================

    def bind_expression(self, expression: Expression) -> BoundExpression:
        if isinstance(expression, LiteralExpression):
            return self._bind_literal_expression(expression)
        if isinstance(expression, VariableExpression):
            return self._bind_variable_expression(expression)
        if isinstance(expression, GroupingExpression):
            return self.bind_expression(expression.expression)
        if isinstance(expression, UnaryExpression):
            return self._bind_unary_expression(expression)
        if isinstance(expression, BinaryExpression):
            return self._bind_binary_expression(expression)
        if isinstance(expression, AssignmentExpression):
            return self._bind_assignment_expression(expression)
        return BoundLiteralExpression(None, TypeUnknown)

    def _bind_literal_expression(self, expression: LiteralExpression) -> BoundLiteralExpression:
        val = expression.value
        if isinstance(val, bool):
            return BoundLiteralExpression(val, TypeBool)
        if isinstance(val, int):
            return BoundLiteralExpression(val, TypeInt)
        if isinstance(val, float):
            return BoundLiteralExpression(val, TypeDouble)
        if isinstance(val, str):
            return BoundLiteralExpression(val, TypeString)
        if val is None:
            return BoundLiteralExpression(None, TypeVoid)
        return BoundLiteralExpression(val, TypeUnknown)

    def _bind_variable_expression(self, expression: VariableExpression) -> BoundExpression:
        name = expression.identifier_token.text
        symbol = self._current_scope.lookup(name)
        if symbol is None or not isinstance(symbol, VariableSymbol):
            self.diagnostics.report_undefined_variable(expression.identifier_token.span, name)
            return BoundLiteralExpression(None, TypeUnknown)
        return BoundVariableExpression(symbol)

    def _bind_assignment_expression(self, expression: AssignmentExpression) -> BoundExpression:
        name = expression.identifier_token.text
        symbol = self._current_scope.lookup(name)
        if symbol is None or not isinstance(symbol, VariableSymbol):
            self.diagnostics.report_undefined_variable(expression.identifier_token.span, name)
            return BoundLiteralExpression(None, TypeUnknown)

        if symbol.is_read_only:
            self.diagnostics.report_cannot_assign_to_constant(expression.identifier_token.span, name)

        bound_right = self.bind_expression(expression.value)
        if not can_convert(bound_right.type, symbol.type):
            self.diagnostics.report_cannot_convert(expression.value.span, str(bound_right.type), str(symbol.type))

        return BoundAssignmentExpression(symbol, bound_right, expression.operator_token.text)

    def _bind_unary_expression(self, expression: UnaryExpression) -> BoundExpression:
        operand = self.bind_expression(expression.operand)
        op_tok = expression.operator_token

        # Increment / Decrement
        if op_tok.kind in (SyntaxKind.PlusPlusToken, SyntaxKind.MinusMinusToken):
            if not isinstance(operand, BoundVariableExpression):
                self.diagnostics.report(expression.span, "Increment/decrement operand must be a variable.")
                return operand
            if not is_numeric(operand.type):
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator(op_tok.text, operand.type, operand.type)
            return BoundUnaryExpression(op, operand, is_postfix=expression.is_postfix)

        # Logical Not
        if op_tok.kind == SyntaxKind.BangToken:
            if not can_convert(operand.type, TypeBool):
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator("!", TypeBool, TypeBool)
            return BoundUnaryExpression(op, operand, is_postfix=False)

        # Bitwise Not
        if op_tok.kind == SyntaxKind.TildeToken:
            if operand.type != TypeInt:
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator("~", TypeInt, TypeInt)
            return BoundUnaryExpression(op, operand, is_postfix=False)

        # Unary + or -
        if op_tok.kind in (SyntaxKind.PlusToken, SyntaxKind.MinusToken):
            if not is_numeric(operand.type):
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator(op_tok.text, operand.type, operand.type)
            return BoundUnaryExpression(op, operand, is_postfix=False)

        self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
        return operand

    def _bind_binary_expression(self, expression: BinaryExpression) -> BoundExpression:
        left = self.bind_expression(expression.left)
        right = self.bind_expression(expression.right)
        op_tok = expression.operator_token

        # String concatenation
        if op_tok.kind == SyntaxKind.PlusToken and (left.type == TypeString or right.type == TypeString):
            op = BoundBinaryOperator("+", left.type, right.type, TypeString)
            return BoundBinaryExpression(left, op, right)

        # Numeric arithmetic: +, -, *, /, %, **
        if op_tok.kind in (
            SyntaxKind.PlusToken,
            SyntaxKind.MinusToken,
            SyntaxKind.StarToken,
            SyntaxKind.SlashToken,
            SyntaxKind.PercentToken,
            SyntaxKind.DoubleStarToken,
        ):
            if is_numeric(left.type) and is_numeric(right.type):
                res_type = get_promoted_numeric_type(left.type, right.type)
                op = BoundBinaryOperator(op_tok.text, left.type, right.type, res_type)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Relational: <, <=, >, >=
        if op_tok.kind in (
            SyntaxKind.LessToken,
            SyntaxKind.LessOrEqualsToken,
            SyntaxKind.GreaterToken,
            SyntaxKind.GreaterOrEqualsToken,
        ):
            if is_numeric(left.type) and is_numeric(right.type):
                op = BoundBinaryOperator(op_tok.text, left.type, right.type, TypeBool)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Equality: ==, !=
        if op_tok.kind in (SyntaxKind.EqualsEqualsToken, SyntaxKind.BangEqualsToken):
            if can_convert(left.type, right.type) or can_convert(right.type, left.type):
                op = BoundBinaryOperator(op_tok.text, left.type, right.type, TypeBool)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Logical: &&, ||
        if op_tok.kind in (SyntaxKind.AmpersandAmpersandToken, SyntaxKind.PipePipeToken):
            if can_convert(left.type, TypeBool) and can_convert(right.type, TypeBool):
                op = BoundBinaryOperator(op_tok.text, TypeBool, TypeBool, TypeBool)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Bitwise: &, |, ^, <<, >>
        if op_tok.kind in (
            SyntaxKind.AmpersandToken,
            SyntaxKind.PipeToken,
            SyntaxKind.HatToken,
            SyntaxKind.LeftShiftToken,
            SyntaxKind.RightShiftToken,
        ):
            if left.type == TypeInt and right.type == TypeInt:
                op = BoundBinaryOperator(op_tok.text, TypeInt, TypeInt, TypeInt)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
        return left
