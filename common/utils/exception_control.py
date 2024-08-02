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


class HemeraBaseException(Exception):
    def __init__(self, message):
        self.crashable = None
        self.retriable = None
        self.message = message
        super().__init__(message)


class RetriableError(HemeraBaseException):
    def __init__(self, message=""):
        self.crashable = False
        self.retriable = True
        self.message = message
        super().__init__(message)


class HistoryUnavailableError(HemeraBaseException):
    def __init__(self, message=""):
        self.crashable = False
        self.retriable = False
        self.message = message
        super().__init__(message)


class NoBatchModeError(HemeraBaseException):
    def __init__(self, message=""):
        self.crashable = False
        self.retriable = True
        self.message = message
        super().__init__(message)


class RPCNotReachable(HemeraBaseException):

    def __init__(self, message=""):
        self.crashable = True
        self.retriable = False
        self.message = message
        super().__init__(message)


class FastShutdownError(HemeraBaseException):
    def __init__(self, message=""):
        self.crashable = True
        self.retriable = False
        self.message = message
        super().__init__(message)


class ErrorRollupError(Exception):
    def __init__(self, message="Invalid rollup type", code=404):
        super().__init__(message)
        self.code = code


# -32700	        Parse error	            Invalid JSON was received by the server.
#                                           An error occurred on the server while parsing the JSON text.
# -32600	        Invalid Request	        The JSON sent is not a valid Request object.
# -32601	        Method not found	    The method does not exist / is not available.
# -32602	        Invalid params	        Invalid method parameter(s).
# -32603	        Internal error	        Internal JSON-RPC error.
# -32000 to -32099	Server error	        Reserved for implementation-defined server-errors.
def decode_response_error(error):
    code = error["code"] if "code" in error else 0
    message = error["message"] if "message" in error else ""

    if code == -32000:
        if message == "execution reverted" or message == "out of gas" or "invalid opcode: INVALID":
            return None
        elif message.find("required historical state unavailable") != -1:
            raise HistoryUnavailableError(message)
        else:
            print(error)
            raise RPCNotReachable(message)
    elif code == -32700 or code == -32600 or code == -32602:
        raise FastShutdownError(message)
    elif (-32000 > code >= -32099) or code == -32603:
        raise RetriableError(message)
    else:
        return None
