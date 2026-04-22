class SdkError(Exception):
    pass


class ValidationError(SdkError, ValueError):
    pass


class NotSupportedError(SdkError, NotImplementedError):
    pass


class ApiError(SdkError):
    pass


class ApiNotAuthorizedError(ApiError):
    pass


class ApiRateLimitError(ApiError):
    pass
