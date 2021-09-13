from dataclasses import dataclass
from codeanalysis.Syntax.syntaxkind import SyntaxKind
from codeanalysis.Syntax.syntaxmap import keyword_map


@dataclass
class SyntaxToken:
    kind: SyntaxKind = None
    value: any = None
    
    def __repr__(self):
        return self.kind.name + (f":{self.value}" if self.value is not None else "")

    def check_keyword(self, word):
        for kind in SyntaxKind:
            if self.is_a_keyword(word) and 100 <= kind.value < 300:
                return self.get_keyword(word)
    
    def is_a_keyword(self, word):
        return word in keyword_map

    def get_keyword(self, word):
        return keyword_map[word]