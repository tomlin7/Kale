from dataclasses import dataclass

@dataclass(frozen=True)
class TextLocation:
    """Represents a 1-based line and 1-based column position in source text."""
    line: int
    column: int

    def __repr__(self) -> str:
        return f"{self.line}:{self.column}"
