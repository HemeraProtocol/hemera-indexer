from werkzeug.exceptions import HTTPException


class APIError(HTTPException):
    """All custom API Exceptions"""

    code = 400

    def __init__(self, message, code=None, detail=None, error_type=None):
        super().__init__()
        self.message = message
        if code is not None:
            self.code = code
        self.detail = detail
        self.error_type = error_type

    def to_dict(self):
        return {
            "message": self.message,
            "code": self.code,
            "details": self.detail,
            "error_type": self.error_type,
        }
