import bisect
from .text_span import TextSpan
from .text_location import TextLocation
from .diagnostic import Diagnostic

class SourceText:
    """Encapsulates source code text and supports line/column mapping and error rendering."""
    def __init__(self, text: str, file_name: str = "<source>"):
        self.text = text
        self.file_name = file_name
        self._line_starts = self._compute_line_starts(text)

    def _compute_line_starts(self, text: str) -> list[int]:
        line_starts = [0]
        for i, char in enumerate(text):
            if char == '\n':
                line_starts.append(i + 1)
        return line_starts

    def get_location(self, position: int) -> TextLocation:
        """Converts an absolute character index into a 1-based TextLocation (line, column)."""
        if position < 0:
            position = 0
        if position > len(self.text):
            position = len(self.text)

        line_index = bisect.bisect_right(self._line_starts, position) - 1
        line_start = self._line_starts[line_index]
        column = position - line_start + 1
        return TextLocation(line=line_index + 1, column=column)

    def get_line_text(self, line_number: int) -> str:
        """Returns the raw text of the 1-based line number without trailing newline."""
        if line_number < 1 or line_number > len(self._line_starts):
            return ""
        start = self._line_starts[line_number - 1]
        if line_number < len(self._line_starts):
            end = self._line_starts[line_number]
        else:
            end = len(self.text)
        return self.text[start:end].rstrip('\r\n')

    def format_diagnostic(self, diagnostic: Diagnostic, use_color: bool = True) -> str:
        """Formats a diagnostic with file, line, col, code snippet, and carets."""
        loc = self.get_location(diagnostic.span.start)
        line_str = self.get_line_text(loc.line)
        
        red = "\033[91m" if use_color else ""
        yellow = "\033[93m" if use_color else ""
        cyan = "\033[96m" if use_color else ""
        reset = "\033[0m" if use_color else ""
        bold = "\033[1m" if use_color else ""

        color = red if diagnostic.severity.value == "error" else yellow

        header = f"{bold}{self.file_name}:{loc.line}:{loc.column}: {color}{diagnostic.severity.value}:{reset}{bold} {diagnostic.message}{reset}"
        
        # Source snippet
        line_num_str = f"{loc.line:>4} | "
        src_line = f"{cyan}{line_num_str}{reset}{line_str}"
        
        # Caret pointer
        indent = " " * (len(line_num_str) - 3 + loc.column)
        caret_len = max(1, min(diagnostic.span.length, len(line_str) - loc.column + 1))
        carets = f"{color}{'^' * caret_len}{reset}"
        pointer_line = f"{' ' * (len(line_num_str) - 3)}| {indent}{carets}"

        return f"{header}\n{src_line}\n{pointer_line}"

    def __len__(self) -> int:
        return len(self.text)

    def __getitem__(self, index: int) -> str:
        return self.text[index]
