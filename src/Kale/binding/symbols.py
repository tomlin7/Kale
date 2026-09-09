from dataclasses import dataclass
from .types import TypeSymbol

@dataclass(frozen=True)
class Symbol:
    name: str
    type: TypeSymbol

@dataclass(frozen=True)
class VariableSymbol(Symbol):
    is_read_only: bool = False

    def __repr__(self) -> str:
        ro = "const " if self.is_read_only else ""
        return f"VariableSymbol({ro}{self.name}: {self.type})"

@dataclass(frozen=True)
class FunctionSymbol(Symbol):
    parameter_types: tuple[TypeSymbol, ...] = ()

    def __repr__(self) -> str:
        params = ", ".join(str(p) for p in self.parameter_types)
        return f"FunctionSymbol({self.name}({params}): {self.type})"
