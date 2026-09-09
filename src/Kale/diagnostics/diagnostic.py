import enum
from dataclasses import dataclass
from .text_span import TextSpan
from .text_location import TextLocation

class DiagnosticSeverity(enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass(frozen=True)
class Diagnostic:
    span: TextSpan
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    location: TextLocation | None = None

    def __str__(self) -> str:
        loc_prefix = f"[{self.location}] " if self.location else ""
        return f"{loc_prefix}{self.severity.value}: {self.message}"
