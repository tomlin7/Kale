import enum


class TokenKind(enum.Enum):
    # Literals
    # ----
    BADTOKEN        = -2
    EOF             = -1
    NEWLINE         = 0
    WHITESPACE      = 1
    NUMBER          = 2
    IDENT           = 3
    STRING          = 4

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


    # Punctuators
    # ----
    LPAR            = 201
    RPAR            = 202
    LSQB            = 203
    RSQB            = 204
    COLON           = 205
    COMMA           = 206
    SEMI            = 207
    
    PLUS            = 208
    MINUS           = 209
    STAR            = 210
    SLASH           = 211
    VBAR            = 212
    AMPER           = 213
    BANG            = 214
    LESS            = 215
    GREATER         = 216
    EQUAL           = 217
    DOT             = 218
    PERCENT         = 219
    LBRACE          = 220
    RBRACE          = 221
    EQEQUAL         = 222
    BANGEQUAL       = 223
    LESSEQUAL       = 224
    GREATEREQUAL    = 225
    TILDE           = 226
    CIRCUMFLEX      = 227
    LEFTSHIFT       = 228
    RIGHTSHIFT      = 228
    DOUBLESTAR      = 229
    PLUSEQUAL       = 230
    MINEQUAL        = 231
    PLUSPLUS        = 232
    MINUSMINUS      = 233
    STAREQUAL       = 234
    SLASHEQUAL      = 235
    PERCENTEQUAL    = 236
    AMPEREQUAL      = 237
    VBAREQUAL       = 238
    CIRCUMFLEXEQUAL = 239
    LEFTSHIFTEQUAL  = 240
    RIGHTSHIFTEQUAL = 241
    DOUBLESTAREQUAL = 242
