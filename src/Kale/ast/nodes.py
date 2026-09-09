from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass
from ..syntax.syntax_token import SyntaxToken
from ..diagnostics.text_span import TextSpan

class SyntaxNode(ABC):
    """Abstract base class for all AST nodes."""
    @property
    @abstractmethod
    def span(self) -> TextSpan:
        pass

    @abstractmethod
    def children(self) -> list["SyntaxNode | SyntaxToken"]:
        pass

# ==========================================
# Expressions
# ==========================================

class Expression(SyntaxNode, ABC):
    """Base class for all expression nodes."""
    pass

@dataclass(frozen=True)
class LiteralExpression(Expression):
    literal_token: SyntaxToken
    value: Any

    @property
    def span(self) -> TextSpan:
        return self.literal_token.span

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.literal_token]

@dataclass(frozen=True)
class VariableExpression(Expression):
    identifier_token: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return self.identifier_token.span

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.identifier_token]

@dataclass(frozen=True)
class GroupingExpression(Expression):
    open_paren: SyntaxToken
    expression: Expression
    close_paren: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.open_paren.span.start, self.close_paren.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.open_paren, self.expression, self.close_paren]

@dataclass(frozen=True)
class CastExpression(Expression):
    target_type_token: SyntaxToken
    expression: Expression
    as_token: SyntaxToken | None = None # If using `expr as Type`
    open_paren: SyntaxToken | None = None # If using `(Type)expr`
    close_paren: SyntaxToken | None = None

    @property
    def span(self) -> TextSpan:
        if self.open_paren:
            return TextSpan.from_bounds(self.open_paren.span.start, self.expression.span.end)
        if self.as_token:
            return TextSpan.from_bounds(self.expression.span.start, self.target_type_token.span.end)
        return TextSpan.from_bounds(self.target_type_token.span.start, self.expression.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        c: list[SyntaxNode | SyntaxToken] = []
        if self.open_paren:
            c.append(self.open_paren)
        c.append(self.target_type_token)
        if self.close_paren:
            c.append(self.close_paren)
        if self.as_token:
            c.append(self.as_token)
        c.append(self.expression)
        return c

@dataclass(frozen=True)
class UnaryExpression(Expression):
    operator_token: SyntaxToken
    operand: Expression
    is_postfix: bool = False

    @property
    def span(self) -> TextSpan:
        if self.is_postfix:
            return TextSpan.from_bounds(self.operand.span.start, self.operator_token.span.end)
        return TextSpan.from_bounds(self.operator_token.span.start, self.operand.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        if self.is_postfix:
            return [self.operand, self.operator_token]
        return [self.operator_token, self.operand]

@dataclass(frozen=True)
class BinaryExpression(Expression):
    left: Expression
    operator_token: SyntaxToken
    right: Expression

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.left.span.start, self.right.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.left, self.operator_token, self.right]

@dataclass(frozen=True)
class AssignmentExpression(Expression):
    identifier_token: SyntaxToken
    operator_token: SyntaxToken
    value: Expression

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.identifier_token.span.start, self.value.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.identifier_token, self.operator_token, self.value]

@dataclass(frozen=True)
class DereferenceAssignmentExpression(Expression):
    target: Expression
    operator_token: SyntaxToken
    value: Expression

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.value.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.operator_token, self.value]

@dataclass(frozen=True)
class CallExpression(Expression):
    callee: SyntaxToken | Expression
    open_paren: SyntaxToken
    arguments: list[Expression]
    close_paren: SyntaxToken

    @property
    def callee_token(self) -> SyntaxToken | None:
        """Backward compatibility property if callee is a SyntaxToken."""
        return self.callee if isinstance(self.callee, SyntaxToken) else None

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.callee.span.start, self.close_paren.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.callee, self.open_paren, *self.arguments, self.close_paren]

@dataclass(frozen=True)
class ArrayLiteralExpression(Expression):
    open_bracket: SyntaxToken
    elements: list[Expression]
    close_bracket: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.open_bracket.span.start, self.close_bracket.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.open_bracket, *self.elements, self.close_bracket]

@dataclass(frozen=True)
class IndexExpression(Expression):
    target: Expression
    open_bracket: SyntaxToken
    index: Expression
    close_bracket: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.close_bracket.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.open_bracket, self.index, self.close_bracket]

@dataclass(frozen=True)
class IndexAssignmentExpression(Expression):
    target: Expression
    open_bracket: SyntaxToken
    index: Expression
    close_bracket: SyntaxToken
    operator_token: SyntaxToken
    value: Expression

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.value.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.open_bracket, self.index, self.close_bracket, self.operator_token, self.value]

@dataclass(frozen=True)
class MemberAccessExpression(Expression):
    target: Expression
    dot_token: SyntaxToken
    member_token: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.member_token.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.dot_token, self.member_token]

@dataclass(frozen=True)
class MemberAssignmentExpression(Expression):
    target: Expression
    dot_token: SyntaxToken
    member_token: SyntaxToken
    operator_token: SyntaxToken
    value: Expression

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.value.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.dot_token, self.member_token, self.operator_token, self.value]

@dataclass(frozen=True)
class ArrowAccessExpression(Expression):
    target: Expression
    arrow_token: SyntaxToken
    member_token: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.member_token.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.arrow_token, self.member_token]

@dataclass(frozen=True)
class ArrowAssignmentExpression(Expression):
    target: Expression
    arrow_token: SyntaxToken
    member_token: SyntaxToken
    operator_token: SyntaxToken
    value: Expression

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.target.span.start, self.value.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.target, self.arrow_token, self.member_token, self.operator_token, self.value]

@dataclass(frozen=True)
class AllocExpression(Expression):
    alloc_keyword: SyntaxToken
    open_paren: SyntaxToken
    type_token: SyntaxToken
    count_expression: Expression | None
    close_paren: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.alloc_keyword.span.start, self.close_paren.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.alloc_keyword, self.open_paren, self.type_token]
        if self.count_expression:
            items.append(self.count_expression)
        items.append(self.close_paren)
        return items

# ==========================================
# Statements
# ==========================================

class Statement(SyntaxNode, ABC):
    """Base class for all statement nodes."""
    pass

@dataclass(frozen=True)
class BlockStatement(Statement):
    open_brace: SyntaxToken
    statements: list[Statement]
    close_brace: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.open_brace.span.start, self.close_brace.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.open_brace, *self.statements, self.close_brace]

@dataclass(frozen=True)
class ParameterNode(SyntaxNode):
    type_token: SyntaxToken
    identifier_token: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.type_token.span.start, self.identifier_token.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.type_token, self.identifier_token]

@dataclass(frozen=True)
class StructFieldNode(SyntaxNode):
    type_token: SyntaxToken
    identifier_token: SyntaxToken
    semicolon_token: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.type_token.span.start, self.semicolon_token.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.type_token, self.identifier_token, self.semicolon_token]

@dataclass(frozen=True)
class StructDeclarationStatement(Statement):
    struct_keyword: SyntaxToken
    identifier_token: SyntaxToken
    open_brace: SyntaxToken
    fields: list[StructFieldNode]
    close_brace: SyntaxToken

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.struct_keyword.span.start, self.close_brace.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.struct_keyword, self.identifier_token, self.open_brace, *self.fields, self.close_brace]

@dataclass(frozen=True)
class FunctionDeclarationStatement(Statement):
    return_type_token: SyntaxToken
    identifier_token: SyntaxToken
    open_paren: SyntaxToken
    parameters: list[ParameterNode]
    close_paren: SyntaxToken
    body: BlockStatement

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.return_type_token.span.start, self.body.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [
            self.return_type_token,
            self.identifier_token,
            self.open_paren,
            *self.parameters,
            self.close_paren,
            self.body,
        ]

@dataclass(frozen=True)
class VariableDeclarationStatement(Statement):
    type_token: SyntaxToken
    identifier_token: SyntaxToken
    equals_token: SyntaxToken | None
    initializer: Expression | None
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else (
            self.initializer.span.end if self.initializer else self.identifier_token.span.end
        )
        return TextSpan.from_bounds(self.type_token.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.type_token, self.identifier_token]
        if self.equals_token:
            items.append(self.equals_token)
        if self.initializer:
            items.append(self.initializer)
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class ExpressionStatement(Statement):
    expression: Expression
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else self.expression.span.end
        return TextSpan.from_bounds(self.expression.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.expression]
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class IfStatement(Statement):
    if_keyword: SyntaxToken
    open_paren: SyntaxToken
    condition: Expression
    close_paren: SyntaxToken
    then_statement: Statement
    else_clause: "ElseClause | None"

    @property
    def span(self) -> TextSpan:
        end = self.else_clause.span.end if self.else_clause else self.then_statement.span.end
        return TextSpan.from_bounds(self.if_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [
            self.if_keyword, self.open_paren, self.condition, self.close_paren, self.then_statement
        ]
        if self.else_clause:
            items.append(self.else_clause)
        return items

@dataclass(frozen=True)
class ElseClause(SyntaxNode):
    else_keyword: SyntaxToken
    statement: Statement

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.else_keyword.span.start, self.statement.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.else_keyword, self.statement]

@dataclass(frozen=True)
class WhileStatement(Statement):
    while_keyword: SyntaxToken
    open_paren: SyntaxToken
    condition: Expression
    close_paren: SyntaxToken
    body: Statement

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.while_keyword.span.start, self.body.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [self.while_keyword, self.open_paren, self.condition, self.close_paren, self.body]

@dataclass(frozen=True)
class ForStatement(Statement):
    for_keyword: SyntaxToken
    open_paren: SyntaxToken
    initializer: Statement | None
    condition: Expression | None
    second_semicolon: SyntaxToken
    increment: Expression | None
    close_paren: SyntaxToken
    body: Statement

    @property
    def span(self) -> TextSpan:
        return TextSpan.from_bounds(self.for_keyword.span.start, self.body.span.end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.for_keyword, self.open_paren]
        if self.initializer:
            items.append(self.initializer)
        if self.condition:
            items.append(self.condition)
        items.append(self.second_semicolon)
        if self.increment:
            items.append(self.increment)
        items.extend([self.close_paren, self.body])
        return items

@dataclass(frozen=True)
class PrintStatement(Statement):
    print_keyword: SyntaxToken
    open_paren: SyntaxToken
    arguments: list[Expression]
    close_paren: SyntaxToken
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else self.close_paren.span.end
        return TextSpan.from_bounds(self.print_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.print_keyword, self.open_paren, *self.arguments, self.close_paren]
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class ReturnStatement(Statement):
    return_keyword: SyntaxToken
    expression: Expression | None
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else (
            self.expression.span.end if self.expression else self.return_keyword.span.end
        )
        return TextSpan.from_bounds(self.return_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.return_keyword]
        if self.expression:
            items.append(self.expression)
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class BreakStatement(Statement):
    break_keyword: SyntaxToken
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else self.break_keyword.span.end
        return TextSpan.from_bounds(self.break_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.break_keyword]
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class ContinueStatement(Statement):
    continue_keyword: SyntaxToken
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else self.continue_keyword.span.end
        return TextSpan.from_bounds(self.continue_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.continue_keyword]
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class FreeStatement(Statement):
    free_keyword: SyntaxToken
    open_paren: SyntaxToken
    expression: Expression
    close_paren: SyntaxToken
    semicolon_token: SyntaxToken | None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else self.close_paren.span.end
        return TextSpan.from_bounds(self.free_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.free_keyword, self.open_paren, self.expression, self.close_paren]
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class ImportStatement(Statement):
    import_keyword: SyntaxToken
    module_path_token: SyntaxToken
    as_keyword: SyntaxToken | None = None
    alias_token: SyntaxToken | None = None
    semicolon_token: SyntaxToken | None = None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else (
            self.alias_token.span.end if self.alias_token else self.module_path_token.span.end
        )
        return TextSpan.from_bounds(self.import_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.import_keyword, self.module_path_token]
        if self.as_keyword:
            items.append(self.as_keyword)
        if self.alias_token:
            items.append(self.alias_token)
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class FromImportStatement(Statement):
    from_keyword: SyntaxToken
    module_path_token: SyntaxToken
    import_keyword: SyntaxToken
    imported_symbols: list[SyntaxToken]
    semicolon_token: SyntaxToken | None = None

    @property
    def span(self) -> TextSpan:
        end = self.semicolon_token.span.end if self.semicolon_token else (
            self.imported_symbols[-1].span.end if self.imported_symbols else self.import_keyword.span.end
        )
        return TextSpan.from_bounds(self.from_keyword.span.start, end)

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        items: list[SyntaxNode | SyntaxToken] = [self.from_keyword, self.module_path_token, self.import_keyword]
        items.extend(self.imported_symbols)
        if self.semicolon_token:
            items.append(self.semicolon_token)
        return items

@dataclass(frozen=True)
class CompilationUnit(SyntaxNode):
    statements: list[Statement]
    end_of_file_token: SyntaxToken

    @property
    def span(self) -> TextSpan:
        if self.statements:
            return TextSpan.from_bounds(self.statements[0].span.start, self.end_of_file_token.span.end)
        return self.end_of_file_token.span

    def children(self) -> list[SyntaxNode | SyntaxToken]:
        return [*self.statements, self.end_of_file_token]
