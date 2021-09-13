from CodeAnalysis.Exceptions.error import Error

class IllegalCharacterException(Error):
    def __init__(self, char):
        self.char = char
        super().__init__(self.char)
