class X10Error(Exception):
    pass


class SdkError(X10Error):
    pass


class SdkValidationError(SdkError, ValueError):
    pass


class SdkNotImplementedError(SdkError, NotImplementedError):
    pass


class ApiError(X10Error):
    pass


class ApiNotAuthorizedError(ApiError):
    pass


class ApiRateLimitError(ApiError):
    pass
