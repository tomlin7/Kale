import enum


class TokenKind(enum.Enum):
    # Meta
    # ----
    BadToken = -2
    EndOfFileToken = -1

    # Literals
    # ----
    NewLineToken        = 0
    WhiteSpaceToken     = 1
    NumberToken       = 2
    StringToken       = 4

    # Identifiers
    IdentifierToken     = 100

    # Keywords
    # ----
    ElseKeyword        = 117
    ForKeyword         = 118
    ForeachKeyword     = 119
    GotoKeyword        = 120
    IfKeyword          = 121
    InKeyword          = 122
    InputKeyword       = 123
    LabelKeyword       = 124
    LetKeyword         = 125
    PrintKeyword       = 126
    VarKeyword         = 127
    WhileKeyword       = 128

    # Type keywords
    IntKeyword             = 200
    FloatKeyword           = 201
    CharKeyword            = 202
    StringKeyword          = 203

    # Punctuators
    # ----
    LPAR            = 301
    RPAR            = 302
    LSQB            = 303
    RSQB            = 304
    COMMA           = 305
    SEMI            = 306
    LBRACE          = 307
    RBRACE          = 308

    PLUS            = 309
    MINUS           = 310
    STAR            = 311
    SLASH           = 312
    VBAR            = 313
    AMPER           = 314
    BANG            = 315
    LESS            = 316
    GREATER         = 317
    EQUAL           = 318
    COLON           = 319
    DOT             = 320
    PERCENT         = 321
    EQEQUAL         = 322
    BANGEQUAL       = 323
    LESSEQUAL       = 324
    GREATEREQUAL    = 325
    TILDE           = 326
    CIRCUMFLEX      = 327
    LEFTSHIFT       = 328
    RIGHTSHIFT      = 329
    DOUBLESTAR      = 330
    PLUSEQUAL       = 331
    MINEQUAL        = 332
    PLUSPLUS        = 333
    MINUSMINUS      = 334
    STAREQUAL       = 335
    SLASHEQUAL      = 336
    PERCENTEQUAL    = 337
    AMPEREQUAL      = 338
    VBAREQUAL       = 339
    CIRCUMFLEXEQUAL = 341
    LEFTSHIFTEQUAL  = 342
    RIGHTSHIFTEQUAL = 343
    DOUBLESTAREQUAL = 344
