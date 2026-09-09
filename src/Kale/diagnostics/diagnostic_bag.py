from typing import Iterator
from .text_span import TextSpan
from .diagnostic import Diagnostic, DiagnosticSeverity

class DiagnosticBag:
    """Collects compiler errors and warnings throughout compilation phases."""
    def __init__(self):
        self._diagnostics: list[Diagnostic] = []

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self._diagnostics)

    def __len__(self) -> int:
        return len(self._diagnostics)

    def __bool__(self) -> bool:
        return len(self._diagnostics) > 0

    @property
    def has_errors(self) -> bool:
        return any(d.severity == DiagnosticSeverity.ERROR for d in self._diagnostics)

    def report(self, span: TextSpan, message: str, severity: DiagnosticSeverity = DiagnosticSeverity.ERROR):
        self._diagnostics.append(Diagnostic(span=span, message=message, severity=severity))

    # Lexer diagnostics
    def report_bad_character(self, span: TextSpan, char: str):
        self.report(span, f"Bad character in input: '{char}'")

    def report_unterminated_string(self, span: TextSpan):
        self.report(span, "Unterminated string literal.")

    def report_invalid_escape_sequence(self, span: TextSpan, char: str):
        self.report(span, f"Invalid escape sequence: '\\{char}'")

    def report_invalid_number(self, span: TextSpan, text: str):
        self.report(span, f"The number '{text}' is not valid.")

    # Parser diagnostics
    def report_unexpected_token(self, span: TextSpan, actual_kind: str, expected_kind: str):
        self.report(span, f"Unexpected token <{actual_kind}>, expected <{expected_kind}>.")

    # Semantic diagnostics
    def report_undefined_variable(self, span: TextSpan, name: str):
        self.report(span, f"Variable '{name}' does not exist in the current scope.")

    def report_variable_already_declared(self, span: TextSpan, name: str):
        self.report(span, f"Variable '{name}' is already declared in this scope.")

    def report_cannot_assign_to_constant(self, span: TextSpan, name: str):
        self.report(span, f"Cannot reassign to read-only variable '{name}'.")

    def report_cannot_convert(self, span: TextSpan, from_type: str, to_type: str):
        self.report(span, f"Cannot convert type '{from_type}' to '{to_type}'.")

    def report_undefined_unary_operator(self, span: TextSpan, op_text: str, operand_type: str):
        self.report(span, f"Unary operator '{op_text}' is not defined for type '{operand_type}'.")

    def report_undefined_binary_operator(self, span: TextSpan, op_text: str, left_type: str, right_type: str):
        self.report(span, f"Binary operator '{op_text}' is not defined for types '{left_type}' and '{right_type}'.")
