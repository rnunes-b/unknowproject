class BotUnauthorizedException(Exception):
    def __init__(self, message, name="UnauthorizedException"):
        self.name = name
        self.message = message
        super().__init__(message)
