class BotProposalInfoException(Exception):
    def __init__(self, message):
        self.name = ("ProposalInfoException",)
        self.message = message
        super().__init__(message)
