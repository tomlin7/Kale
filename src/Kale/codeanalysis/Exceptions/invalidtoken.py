from codeanalysis.Exceptions.error import Error


class InvalidTokenException(Error):
    def __init__(self, token):
        self.token = token
        super().__init__(self.token)