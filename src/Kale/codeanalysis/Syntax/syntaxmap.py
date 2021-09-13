from codeanalysis.Syntax.tokenkind import TokenKind

keyword_map = {
    'char'      : TokenKind.CharKeyword,
    'else'      : TokenKind.ElseKeyword,
    'float'     : TokenKind.FloatKeyword,
    'for'       : TokenKind.ForKeyword,
    'foreach'   : TokenKind.ForeachKeyword,
    'goto'      : TokenKind.GotoKeyword,
    'if'        : TokenKind.IfKeyword,
    'in'        : TokenKind.InKeyword,
    'input'     : TokenKind.InputKeyword,
    'int'       : TokenKind.IntKeyword,
    'label'     : TokenKind.LabelKeyword,
    'let'       : TokenKind.LetKeyword,
    'print'     : TokenKind.PrintKeyword,
    'string'    : TokenKind.StringToken,
    'var'       : TokenKind.VarKeyword,
    'while'     : TokenKind.WhileKeyword,
}
