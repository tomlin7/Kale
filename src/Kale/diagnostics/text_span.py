from dataclasses import dataclass

@dataclass(frozen=True)
class TextSpan:
    """Represents a continuous span of text within source code by start index and length."""
    start: int
    length: int

    @property
    def end(self) -> int:
        return self.start + self.length

    @classmethod
    def from_bounds(cls, start: int, end: int) -> "TextSpan":
        return cls(start=start, length=max(0, end - start))

    def __repr__(self) -> str:
        return f"TextSpan({self.start}..{self.end})"
