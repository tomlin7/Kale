from codeanalysis.Syntax.tokenkind import TokenKind

keywords = {
    TokenKind.LABEL: 'label',
    TokenKind.GOTO: 'goto',
    TokenKind.PRINT: 'print',
    TokenKind.LET: 'let',
    TokenKind.VAR: 'var',
    TokenKind.IF: 'if',
    TokenKind.ELSE: 'else',
}

LABEL, GOTO, PRINT, INPUT, LET, VAR, IF, ELSE, WHILE, FOR, FOREACH, IN, INT, FLOAT, CHAR,  STRING