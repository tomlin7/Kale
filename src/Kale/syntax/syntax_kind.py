import enum

class SyntaxKind(enum.Enum):
    # Special
    BadToken = enum.auto()
    EndOfFileToken = enum.auto()
    WhitespaceTrivia = enum.auto()
    NewLineTrivia = enum.auto()
    CommentTrivia = enum.auto()

    # Literals
    NumberToken = enum.auto()
    StringToken = enum.auto()
    CharToken = enum.auto()

    # Identifiers
    IdentifierToken = enum.auto()

    # Keywords - Values
    TrueKeyword = enum.auto()
    FalseKeyword = enum.auto()
    NullKeyword = enum.auto()

    # Keywords - Declarations
    LetKeyword = enum.auto()
    VarKeyword = enum.auto()
    ConstKeyword = enum.auto()
    StructKeyword = enum.auto()

    # Keywords - Control Flow
    IfKeyword = enum.auto()
    ElseKeyword = enum.auto()
    WhileKeyword = enum.auto()
    ForKeyword = enum.auto()
    ReturnKeyword = enum.auto()
    BreakKeyword = enum.auto()
    ContinueKeyword = enum.auto()
    GotoKeyword = enum.auto()
    LabelKeyword = enum.auto()

    # Keywords - Built-in functions/statements
    PrintKeyword = enum.auto()
    InputKeyword = enum.auto()

    # Keywords - Types
    IntKeyword = enum.auto()
    FloatKeyword = enum.auto()
    DoubleKeyword = enum.auto()
    StringKeyword = enum.auto()
    BoolKeyword = enum.auto()
    CharKeyword = enum.auto()
    VoidKeyword = enum.auto()

    # Punctuators
    OpenParenthesisToken = enum.auto()    # (
    CloseParenthesisToken = enum.auto()   # )
    OpenBraceToken = enum.auto()          # {
    CloseBraceToken = enum.auto()         # }
    OpenBracketToken = enum.auto()        # [
    CloseBracketToken = enum.auto()       # ]
    CommaToken = enum.auto()              # ,
    SemicolonToken = enum.auto()          # ;
    ColonToken = enum.auto()              # :
    DotToken = enum.auto()                # .

    # Operators - Arithmetic
    PlusToken = enum.auto()               # +
    MinusToken = enum.auto()              # -
    StarToken = enum.auto()               # *
    SlashToken = enum.auto()              # /
    PercentToken = enum.auto()            # %
    DoubleStarToken = enum.auto()         # **

    # Operators - Relational
    EqualsEqualsToken = enum.auto()       # ==
    BangEqualsToken = enum.auto()         # !=
    LessToken = enum.auto()               # <
    LessOrEqualsToken = enum.auto()       # <=
    GreaterToken = enum.auto()            # >
    GreaterOrEqualsToken = enum.auto()    # >=

    # Operators - Logical
    AmpersandAmpersandToken = enum.auto() # &&
    PipePipeToken = enum.auto()           # ||
    BangToken = enum.auto()               # !

    # Operators - Bitwise
    AmpersandToken = enum.auto()          # &
    PipeToken = enum.auto()               # |
    HatToken = enum.auto()                # ^
    TildeToken = enum.auto()              # ~
    LeftShiftToken = enum.auto()          # <<
    RightShiftToken = enum.auto()         # >>

    # Operators - Increment / Decrement
    PlusPlusToken = enum.auto()           # ++
    MinusMinusToken = enum.auto()         # --

    # Operators - Assignment
    EqualsToken = enum.auto()             # =
    PlusEqualsToken = enum.auto()         # +=
    MinusEqualsToken = enum.auto()        # -=
    StarEqualsToken = enum.auto()         # *=
    SlashEqualsToken = enum.auto()        # /=
    PercentEqualsToken = enum.auto()      # %=
    AmpersandEqualsToken = enum.auto()    # &=
    PipeEqualsToken = enum.auto()         # |=
    HatEqualsToken = enum.auto()          # ^=
    LeftShiftEqualsToken = enum.auto()    # <<=
    RightShiftEqualsToken = enum.auto()   # >>=
