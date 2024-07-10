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


# -32700	        Parse error	            Invalid JSON was received by the server.
#                                           An error occurred on the server while parsing the JSON text.
# -32600	        Invalid Request	        The JSON sent is not a valid Request object.
# -32601	        Method not found	    The method does not exist / is not available.
# -32602	        Invalid params	        Invalid method parameter(s).
# -32603	        Internal error	        Internal JSON-RPC error.
# -32000 to -32099	Server error	        Reserved for implementation-defined server-errors.
def decode_response_error(error):
    code = error['code'] if 'code' in error else 0
    message = error['message'] if 'message' in error else ''

    if code == -32000:
        raise RPCNotReachable(message)
    elif code == -32700 or code == -32600 or code == -32602:
        raise FastShutdownError(message)
    elif (-32000 > code >= -32099) or code == -32603:
        raise RetriableError(message)
    else:
        return None
