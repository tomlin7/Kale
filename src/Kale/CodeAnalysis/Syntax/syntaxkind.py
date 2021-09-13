import enum


class SyntaxKind(enum.Enum):
    # Meta kinds
    # ----
    Comments                = -3
    BadToken                = -2
    EndOfFileToken          = -1

    # Literals
    # ----
    NewLineToken            = 0
    WhiteSpaceToken         = 1
    NumberToken             = 2
    StringToken             = 4

    # Identifiers
    # ----
    IdentifierToken         = 100

    # Keywords: Keywords
    # ----
    ElseKeyword             = 111
    ForKeyword              = 112
    ForeachKeyword          = 113
    GotoKeyword             = 114
    IfKeyword               = 115
    InKeyword               = 116
    InputKeyword            = 117
    LabelKeyword            = 118
    LetKeyword              = 119
    PrintKeyword            = 120
    VarKeyword              = 121
    WhileKeyword            = 122

    # Keywords: Types
    # ----
    BoolKeyword             = 201
    CharKeyword             = 202
    FloatKeyword            = 203
    IntKeyword              = 204
    StringKeyword           = 205

    # Punctuators
    # ----
    OpenParenthesisToken    = 301
    CloseParenthesisToken   = 302
    OpenBracketsToken       = 303
    CloseBracketsToken      = 304
    CommaToken              = 305
    SemicolonToken          = 306
    OpenBraceToken          = 307
    CloseBraceToken         = 308

    # Operators: Single character
    # ----    
    PlusToken               = 351
    MinusToken              = 352
    StartToken              = 353
    SlashToken              = 353
    PipeToken               = 355
    AmpersandToken          = 356
    BangToken               = 357
    LessToken               = 358
    GreaterToken            = 359
    EqualsToken             = 360
    ColonToken              = 361
    DotToken                = 362
    PercentToken            = 363
    TildeToken              = 364
    HatToken                = 365
    
    # Operators: Two characters
    EqualsEqualsToken       = 401
    BangEqualsToken         = 402
    LessOrEqualsToken       = 403
    GreaterOrEqualsToken    = 404
    LeftShiftToken          = 405
    RightShiftToken         = 406
    DoubleStarToken         = 407
    PlusEqualsToken         = 408
    MinusEqualsToken        = 409
    PlusPlusToken           = 410
    MinusMinusToken         = 411
    StarEqualsToken         = 412
    SlashEqualsToken        = 413
    PercentEqualsToken      = 414
    AmpersandEqualsToken    = 415
    PipeEqualsToken         = 416
    HatEqualsToken          = 417

    # Operators: Three characters
    LeftShiftEqualsToken    = 451
    RightShiftEqualsToken   = 452
    DoubleStarEqualsToken   = 453
