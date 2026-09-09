from typing import Any
from dataclasses import dataclass
from ..diagnostics.text_span import TextSpan
from .syntax_kind import SyntaxKind

@dataclass(frozen=True)
class SyntaxToken:
    """Represents an atomic lexical token with its kind, span, literal value, and source text."""
    kind: SyntaxKind
    span: TextSpan
    value: Any = None
    text: str = ""

    def __repr__(self) -> str:
        val_str = f", value={self.value!r}" if self.value is not None else ""
        return f"SyntaxToken({self.kind.name}, text={self.text!r}, span={self.span}{val_str})"
