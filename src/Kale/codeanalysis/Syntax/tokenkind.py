import enum


class TokenKind(enum.Enum):
    # Literals
    # ----
    BADTOKEN        = -2
    EOF             = -1
    NEWLINE         = 0
    WHITESPACE      = 1
    NUMBER          = 2
    STRING          = 4

    # Identifiers
    IDENTIFIER      = 100

    # Keywords
    # ----
    LABEL           = 101
    GOTO            = 102
    PRINT           = 103
    INPUT           = 104
    LET             = 105
    VAR             = 106
    IF              = 107
    ELSE            = 108
    WHILE           = 109
    FOR             = 110
    FOREACH         = 111
    IN              = 112

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
