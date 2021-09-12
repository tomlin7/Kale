from dataclasses import dataclass
from codeanalysis.Syntax.tokenkind import TokenKind

@dataclass
class Token:
    kind: TokenKind
    value: any = None
    
    def __repr__(self):
        return self.kind.name + (f":{self.value}" if self.value is not None else "")

    @staticmethod
    def check_keyword(token_text):
        for kind in TokenKind:
            if kind.name == token_text and 100 <= kind.value < 200:
                return kind
