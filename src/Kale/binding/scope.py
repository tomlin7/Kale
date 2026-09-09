from typing import Optional
from .symbols import Symbol

class Scope:
    """Represents a lexical scope with parent chain for symbols lookup."""
    def __init__(self, parent: Optional["Scope"] = None):
        self.parent = parent
        self._symbols: dict[str, Symbol] = {}

    def try_declare(self, symbol: Symbol) -> bool:
        """Declares a symbol in the current scope. Returns False if already declared locally."""
        if symbol.name in self._symbols:
            return False
        self._symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Symbol | None:
        """Looks up a symbol in this scope or any enclosing parent scopes."""
        if name in self._symbols:
            return self._symbols[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def is_declared_locally(self, name: str) -> bool:
        return name in self._symbols

    def get_local_symbols(self) -> list[Symbol]:
        return list(self._symbols.values())
