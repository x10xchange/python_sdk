class SdkError(Exception):
    pass


class ValidationError(SdkError, ValueError):
    pass


class NotSupportedError(SdkError, NotImplementedError):
    pass


class StreamRpcError(SdkError):
    pass


class StreamRpcServerError(StreamRpcError):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    UNAUTHORIZED = -32001

    def __init__(self, code: int, message: str, data: object = None) -> None:
        super().__init__(f"[{code}] {message}")

        self.code = code
        self.message = message
        self.data = data


class StreamRpcConnectionError(StreamRpcError):
    """
    WebSocket connection is unavailable.
    """


class StreamRpcTimeoutError(StreamRpcError):
    """
    RPC request times out waiting for a response.
    """


class StreamRpcParseError(StreamRpcError):
    """
    Incoming message cannot be parsed as JSON.
    """


class ApiError(SdkError):
    pass


class ApiNotAuthorizedError(ApiError):
    pass


class ApiRateLimitError(ApiError):
    pass
