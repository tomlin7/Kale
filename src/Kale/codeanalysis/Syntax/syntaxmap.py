from codeanalysis.Syntax.syntaxkind import SyntaxKind

keyword_map = {
    'char'      : SyntaxKind.CharKeyword,
    'else'      : SyntaxKind.ElseKeyword,
    'float'     : SyntaxKind.FloatKeyword,
    'for'       : SyntaxKind.ForKeyword,
    'foreach'   : SyntaxKind.ForeachKeyword,
    'goto'      : SyntaxKind.GotoKeyword,
    'if'        : SyntaxKind.IfKeyword,
    'in'        : SyntaxKind.InKeyword,
    'input'     : SyntaxKind.InputKeyword,
    'int'       : SyntaxKind.IntKeyword,
    'label'     : SyntaxKind.LabelKeyword,
    'let'       : SyntaxKind.LetKeyword,
    'print'     : SyntaxKind.PrintKeyword,
    'string'    : SyntaxKind.StringToken,
    'var'       : SyntaxKind.VarKeyword,
    'while'     : SyntaxKind.WhileKeyword,
}
