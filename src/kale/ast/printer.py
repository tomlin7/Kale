import io
from .nodes import SyntaxNode
from ..syntax.syntax_token import SyntaxToken

class AstPrinter:
    """Formats and prints an AST tree structure for debugging and inspection."""
    def __init__(self, use_color: bool = False, use_ascii: bool = False):
        self.use_color = use_color
        self.use_ascii = use_ascii

    def print_node(self, node: SyntaxNode) -> str:
        out = io.StringIO()
        self._print_tree(node, out, indent="", is_last=True)
        return out.getvalue()

    def _print_tree(self, node: SyntaxNode | SyntaxToken, out: io.StringIO, indent: str, is_last: bool):
        if self.use_ascii:
            marker = "\\-- " if is_last else "+-- "
        else:
            marker = "└── " if is_last else "├── "
        out.write(indent)
        out.write(marker)

        if isinstance(node, SyntaxToken):
            val = f" {node.value!r}" if node.value is not None else ""
            txt = f" '{node.text}'" if node.text else ""
            out.write(f"Token: {node.kind.name}{txt}{val}\n")
            return

        out.write(f"{node.__class__.__name__}\n")

        pipe = "|   " if self.use_ascii else "│   "
        indent += "    " if is_last else pipe
        children = node.children()
        for i, child in enumerate(children):
            self._print_tree(child, out, indent, i == len(children) - 1)
