from dataclasses import dataclass
from codeanalysis.Syntax.tokenkind import TokenKind
from codeanalysis.Syntax.tokenmap import keyword_map


@dataclass
class Token:
    kind: TokenKind = None
    value: any = None
    
    def __repr__(self):
        return self.kind.name + (f":{self.value}" if self.value is not None else "")

    def check_keyword(self, token_text):
        for kind in TokenKind:
            if self.is_a_keyword(token_text) and 100 <= kind.value < 300:
                return self.get_keyword(token_text)
    
    def is_a_keyword(self, token_text):
        return token_text in keyword_map

    def get_keyword(self, token_text):
        return keyword_map[token_text]