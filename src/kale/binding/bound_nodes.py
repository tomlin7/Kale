from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from .types import TypeSymbol, StructTypeSymbol, EnumTypeSymbol, ModuleTypeSymbol
from .symbols import Symbol, VariableSymbol, FunctionSymbol, ModuleSymbol
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

@dataclass(frozen=True)
class BoundIndirectCallExpression(BoundExpression):
    callee: BoundExpression
    arguments: list[BoundExpression]
    return_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.return_type

@dataclass(frozen=True)
class BoundFunctionPointerExpression(BoundExpression):
    function: FunctionSymbol
    fn_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.fn_type

@dataclass(frozen=True)
class BoundArrayLiteralExpression(BoundExpression):
    elements: list[BoundExpression]
    array_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.array_type

@dataclass(frozen=True)
class BoundIndexExpression(BoundExpression):
    target: BoundExpression
    index: BoundExpression
    element_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.element_type

@dataclass(frozen=True)
class BoundIndexAssignmentExpression(BoundExpression):
    target: BoundExpression
    index: BoundExpression
    value: BoundExpression
    operator_kind: str = "="

    @property
    def type(self) -> TypeSymbol:
        return self.value.type

@dataclass(frozen=True)
class BoundMemberAccessExpression(BoundExpression):
    target: BoundExpression
    member_name: str
    member_index: int
    member_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.member_type

@dataclass(frozen=True)
class BoundMemberAssignmentExpression(BoundExpression):
    target: BoundExpression
    member_name: str
    member_index: int
    member_type: TypeSymbol
    value: BoundExpression
    operator_kind: str = "="

    @property
    def type(self) -> TypeSymbol:
        return self.member_type

@dataclass(frozen=True)
class BoundAddressOfExpression(BoundExpression):
    operand: BoundExpression
    pointer_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.pointer_type

@dataclass(frozen=True)
class BoundDereferenceExpression(BoundExpression):
    operand: BoundExpression
    target_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.target_type

@dataclass(frozen=True)
class BoundDereferenceAssignmentExpression(BoundExpression):
    operand: BoundExpression
    value: BoundExpression
    operator_kind: str = "="

    @property
    def type(self) -> TypeSymbol:
        return self.value.type

@dataclass(frozen=True)
class BoundAllocExpression(BoundExpression):
    allocated_type: TypeSymbol
    count: BoundExpression | None
    pointer_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.pointer_type

@dataclass(frozen=True)
class BoundCastExpression(BoundExpression):
    expression: BoundExpression
    target_type: TypeSymbol

    @property
    def type(self) -> TypeSymbol:
        return self.target_type

# ==========================================
# Bound Statements
# ==========================================

class BoundStatement(BoundNode, ABC):
    pass

@dataclass(frozen=True)
class BoundStructDeclaration(BoundStatement):
    struct_type: StructTypeSymbol

@dataclass(frozen=True)
class BoundEnumDeclaration(BoundStatement):
    enum_type: EnumTypeSymbol

@dataclass(frozen=True)
class BoundBlockStatement(BoundStatement):
    statements: list[BoundStatement]

@dataclass(frozen=True)
class BoundVariableDeclaration(BoundStatement):
    variable: VariableSymbol
    initializer: BoundExpression | None

@dataclass(frozen=True)
class BoundGlobalVariable(BoundStatement):
    variable: VariableSymbol
    initializer: BoundExpression | None
    module_name: str | None = None  # If from imported module, the module name

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
class BoundSwitchCase(BoundNode):
    case_values: list[BoundExpression]
    body: list[BoundStatement]

@dataclass(frozen=True)
class BoundSwitchStatement(BoundStatement):
    condition: BoundExpression
    cases: list[BoundSwitchCase]
    default_body: list[BoundStatement] | None

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
class BoundFreeStatement(BoundStatement):
    expression: BoundExpression

@dataclass(frozen=True)
class BoundExpressionStatement(BoundStatement):
    expression: BoundExpression

@dataclass(frozen=True)
class BoundFunctionDeclaration(BoundStatement):
    symbol: FunctionSymbol
    body: BoundBlockStatement | None = None

@dataclass(frozen=True)
class BoundImportStatement(BoundStatement):
    module_path: str
    alias: str
    module_symbol: ModuleSymbol

@dataclass(frozen=True)
class BoundProgram(BoundNode):
    statements: list[BoundStatement]
    root_scope: Scope
    functions: list[BoundFunctionDeclaration] = None # type: ignore
    structs: list[BoundStructDeclaration] = None # type: ignore
    enums: list[BoundEnumDeclaration] = None # type: ignore
    module_symbols: dict[str, ModuleSymbol] = None # type: ignore
    globals: list[BoundGlobalVariable] = None # type: ignore

    def __post_init__(self):
        if self.functions is None:
            object.__setattr__(self, "functions", [])
        if self.structs is None:
            object.__setattr__(self, "structs", [])
        if self.enums is None:
            object.__setattr__(self, "enums", [])
        if self.module_symbols is None:
            object.__setattr__(self, "module_symbols", {})
        if self.globals is None:
            object.__setattr__(self, "globals", [])

