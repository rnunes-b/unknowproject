class APIException(Exception):
    def __init__(self, message, status_code=400, error_type="APIError"):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(self.message)

    def __str__(self):
        return f"{self.error_type}: {self.message}"

    def to_dict(self):
        return {
            "error_type": self.error_type,
            "message": self.message,
            "status_code": self.status_code
        }