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
    parameters: tuple[VariableSymbol, ...] = ()
    return_type: TypeSymbol = None  # type: ignore
    mangled_name: str | None = None
    is_extern: bool = False
    is_var_args: bool = False

    def __init__(
        self,
        name: str,
        parameters: tuple[VariableSymbol, ...] = (),
        return_type: TypeSymbol | None = None,
        type: TypeSymbol | None = None,
        mangled_name: str | None = None,
        is_extern: bool = False,
        is_var_args: bool = False,
    ):
        actual_type = return_type if return_type is not None else type
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "type", actual_type)
        object.__setattr__(self, "parameters", parameters)
        object.__setattr__(self, "return_type", actual_type)
        object.__setattr__(self, "mangled_name", mangled_name or name)
        object.__setattr__(self, "is_extern", is_extern)
        object.__setattr__(self, "is_var_args", is_var_args)

    @property
    def parameter_types(self) -> tuple[TypeSymbol, ...]:
        return tuple(p.type for p in self.parameters)

    def __repr__(self) -> str:
        params = ", ".join(f"{p.name}: {p.type}" for p in self.parameters)
        return f"FunctionSymbol({self.name}({params}): {self.type})"

@dataclass(frozen=True)
class ModuleSymbol(Symbol):
    pass

