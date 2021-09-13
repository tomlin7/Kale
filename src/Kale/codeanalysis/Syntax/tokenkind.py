import enum


class TokenKind(enum.Enum):
    # Meta
    # ----
    BadToken                = -2
    EndOfFileToken          = -1

    # Literals
    # ----
    NewLineToken            = 0
    WhiteSpaceToken         = 1
    NumberToken             = 2
    StringToken             = 4

    # Identifiers
    IdentifierToken         = 100

    # Keywords
    # ----
    ElseKeyword             = 117
    ForKeyword              = 118
    ForeachKeyword          = 119
    GotoKeyword             = 120
    IfKeyword               = 121
    InKeyword               = 122
    InputKeyword            = 123
    LabelKeyword            = 124
    LetKeyword              = 125
    PrintKeyword            = 126
    VarKeyword              = 127
    WhileKeyword            = 128

    # Type keywords
    IntKeyword              = 200
    FloatKeyword            = 201
    CharKeyword             = 202
    StringKeyword           = 203

    # Punctuators
    # ----
    OpenParenthesisToken    = 301
    CloseParenthesisToken   = 302
    OpenBracketsToken       = 303
    CloseBracketsToken      = 304
    CommaToken              = 305
    SemiToken               = 306
    OpenBraceToken          = 307
    CloseBraceToken         = 308

    PlusToken               = 309
    MinusToken              = 310
    StartToken              = 311
    SlashToken              = 312
    PipeToken               = 313
    AmpersandToken          = 314
    BangToken               = 315
    LessToken               = 316
    GreaterToken            = 317
    EqualsToken             = 318
    ColonToken              = 319
    DotToken                = 320
    PercentToken            = 321
    EqualsEqualsToken       = 322
    BangEqualsToken         = 323
    LessOrEqualsToken       = 324
    GreaterOrEqualsToken    = 325
    TildeToken              = 326
    HatToken                = 327
    LeftShiftToken          = 328
    RightShiftToken         = 329
    DoubleStarToken         = 330
    PlusEqualsToken         = 331
    MinusEqualsToken        = 332
    PlusPlusToken           = 333
    MinusMinusToken         = 334
    StarEqualsToken         = 335
    SlashEqualsToken        = 336
    PercentEqualsToken      = 337
    AmpereToken             = 338
    PipeEqualsToken         = 339
    HatEqualsToken          = 341
    LeftShiftEqualsToken    = 342
    RightShiftEqualsToken   = 343
    DoubleStarEqualsToken   = 344
