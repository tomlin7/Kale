from .syntax_kind import SyntaxKind

KEYWORDS: dict[str, SyntaxKind] = {
    # Declarations
    "let": SyntaxKind.LetKeyword,
    "var": SyntaxKind.VarKeyword,
    "const": SyntaxKind.ConstKeyword,
    "struct": SyntaxKind.StructKeyword,
    "import": SyntaxKind.ImportKeyword,
    "from": SyntaxKind.FromKeyword,
    "as": SyntaxKind.AsKeyword,

    # Values
    "true": SyntaxKind.TrueKeyword,
    "false": SyntaxKind.FalseKeyword,
    "null": SyntaxKind.NullKeyword,

    # Control Flow
    "if": SyntaxKind.IfKeyword,
    "else": SyntaxKind.ElseKeyword,
    "while": SyntaxKind.WhileKeyword,
    "for": SyntaxKind.ForKeyword,
    "return": SyntaxKind.ReturnKeyword,
    "break": SyntaxKind.BreakKeyword,
    "continue": SyntaxKind.ContinueKeyword,
    "goto": SyntaxKind.GotoKeyword,
    "label": SyntaxKind.LabelKeyword,

    # Builtins
    "print": SyntaxKind.PrintKeyword,
    "input": SyntaxKind.InputKeyword,
    "alloc": SyntaxKind.AllocKeyword,
    "free": SyntaxKind.FreeKeyword,

    # Types
    "int": SyntaxKind.IntKeyword,
    "float": SyntaxKind.FloatKeyword,
    "double": SyntaxKind.DoubleKeyword,
    "string": SyntaxKind.StringKeyword,
    "bool": SyntaxKind.BoolKeyword,
    "char": SyntaxKind.CharKeyword,
    "void": SyntaxKind.VoidKeyword,
}

TYPE_KEYWORDS: set[SyntaxKind] = {
    SyntaxKind.IntKeyword,
    SyntaxKind.FloatKeyword,
    SyntaxKind.DoubleKeyword,
    SyntaxKind.StringKeyword,
    SyntaxKind.BoolKeyword,
    SyntaxKind.CharKeyword,
    SyntaxKind.VoidKeyword,
}

ASSIGNMENT_OPERATORS: set[SyntaxKind] = {
    SyntaxKind.EqualsToken,
    SyntaxKind.PlusEqualsToken,
    SyntaxKind.MinusEqualsToken,
    SyntaxKind.StarEqualsToken,
    SyntaxKind.SlashEqualsToken,
    SyntaxKind.PercentEqualsToken,
    SyntaxKind.AmpersandEqualsToken,
    SyntaxKind.PipeEqualsToken,
    SyntaxKind.HatEqualsToken,
    SyntaxKind.LeftShiftEqualsToken,
    SyntaxKind.RightShiftEqualsToken,
}

def get_keyword_kind(text: str) -> SyntaxKind | None:
    return KEYWORDS.get(text)

def is_type_keyword(kind: SyntaxKind) -> bool:
    return kind in TYPE_KEYWORDS

def is_assignment_operator(kind: SyntaxKind) -> bool:
    return kind in ASSIGNMENT_OPERATORS

def get_unary_operator_precedence(kind: SyntaxKind) -> int:
    """Returns the precedence of a unary operator (higher binds tighter), or 0 if not unary."""
    if kind in (
        SyntaxKind.PlusToken,
        SyntaxKind.MinusToken,
        SyntaxKind.BangToken,
        SyntaxKind.TildeToken,
        SyntaxKind.PlusPlusToken,
        SyntaxKind.MinusMinusToken,
        SyntaxKind.AmpersandToken,  # Address-of &
        SyntaxKind.StarToken,       # Dereference *
    ):
        return 7
    return 0

def get_binary_operator_precedence(kind: SyntaxKind) -> int:
    """Returns the precedence of a binary operator (higher binds tighter), or 0 if not binary."""
    if kind == SyntaxKind.DoubleStarToken:
        return 6
    if kind in (SyntaxKind.StarToken, SyntaxKind.SlashToken, SyntaxKind.PercentToken):
        return 5
    if kind in (SyntaxKind.PlusToken, SyntaxKind.MinusToken):
        return 4
    if kind in (SyntaxKind.LeftShiftToken, SyntaxKind.RightShiftToken):
        return 3
    if kind in (
        SyntaxKind.LessToken,
        SyntaxKind.LessOrEqualsToken,
        SyntaxKind.GreaterToken,
        SyntaxKind.GreaterOrEqualsToken,
    ):
        return 2
    if kind in (SyntaxKind.EqualsEqualsToken, SyntaxKind.BangEqualsToken):
        return 1
    if kind == SyntaxKind.AmpersandToken:
        return 1
    if kind in (SyntaxKind.HatToken, SyntaxKind.CaretToken):
        return 1
    if kind == SyntaxKind.PipeToken:
        return 1
    if kind == SyntaxKind.AmpersandAmpersandToken:
        return 1
    if kind == SyntaxKind.PipePipeToken:
        return 1
    return 0
