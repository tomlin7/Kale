from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from .types import TypeSymbol
from .symbols import VariableSymbol, FunctionSymbol
from .scope import Scope

class BoundNode(ABC):
    """Base class for all bound (semantically analyzed and typed) nodes."""
    pass

# ==========================================
# Bound Operators
# ==========================================

@dataclass(frozen=True)
class BoundUnaryOperator:
    operator_kind: str # "identity", "negation", "logical_not", "bitwise_not", "prefix_inc", "postfix_inc", etc.
    operand_type: TypeSymbol
    result_type: TypeSymbol

@dataclass(frozen=True)
class BoundBinaryOperator:
    operator_kind: str # "add", "sub", "mul", "div", "mod", "pow", "equals", "not_equals", "less", etc.
    left_type: TypeSymbol
    right_type: TypeSymbol
    result_type: TypeSymbol

# ==========================================
# Bound Expressions
# ==========================================

class BoundExpression(BoundNode, ABC):
    @property
    @abstractmethod
    def type(self) -> TypeSymbol:
        pass

@dataclass(frozen=True)
class BoundLiteralExpression(BoundExpression):
    value: Any
    literal_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.literal_type

@dataclass(frozen=True)
class BoundVariableExpression(BoundExpression):
    variable: VariableSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.variable.type

@dataclass(frozen=True)
class BoundAssignmentExpression(BoundExpression):
    variable: VariableSymbol
    expression: BoundExpression
    operator_kind: str = "=" # "=", "+=", "-=", etc.

    @property
    def type(self) -> TypeSymbol:
        return self.variable.type

@dataclass(frozen=True)
class BoundUnaryExpression(BoundExpression):
    operator: BoundUnaryOperator
    operand: BoundExpression
    is_postfix: bool = False

    @property
    def type(self) -> TypeSymbol:
        return self.operator.result_type

@dataclass(frozen=True)
class BoundBinaryExpression(BoundExpression):
    left: BoundExpression
    operator: BoundBinaryOperator
    right: BoundExpression

    @property
    def type(self) -> TypeSymbol:
        return self.operator.result_type

@dataclass(frozen=True)
class BoundCallExpression(BoundExpression):
    function: FunctionSymbol
    arguments: list[BoundExpression]

    @property
    def type(self) -> TypeSymbol:
        return self.function.type

# ==========================================
# Bound Statements
# ==========================================

class BoundStatement(BoundNode, ABC):
    pass

@dataclass(frozen=True)
class BoundBlockStatement(BoundStatement):
    statements: list[BoundStatement]

@dataclass(frozen=True)
class BoundVariableDeclaration(BoundStatement):
    variable: VariableSymbol
    initializer: BoundExpression | None

@dataclass(frozen=True)
class BoundIfStatement(BoundStatement):
    condition: BoundExpression
    then_statement: BoundStatement
    else_statement: BoundStatement | None

@dataclass(frozen=True)
class BoundWhileStatement(BoundStatement):
    condition: BoundExpression
    body: BoundStatement

@dataclass(frozen=True)
class BoundForStatement(BoundStatement):
    initializer: BoundStatement | None
    condition: BoundExpression | None
    increment: BoundExpression | None
    body: BoundStatement

@dataclass(frozen=True)
class BoundPrintStatement(BoundStatement):
    arguments: list[BoundExpression]

@dataclass(frozen=True)
class BoundReturnStatement(BoundStatement):
    expression: BoundExpression | None

@dataclass(frozen=True)
class BoundBreakStatement(BoundStatement):
    pass

@dataclass(frozen=True)
class BoundContinueStatement(BoundStatement):
    pass

@dataclass(frozen=True)
class BoundExpressionStatement(BoundStatement):
    expression: BoundExpression

@dataclass(frozen=True)
class BoundProgram(BoundNode):
    statements: list[BoundStatement]
    root_scope: Scope
