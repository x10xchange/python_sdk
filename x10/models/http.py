from typing import Any, Generic, Optional, Sequence, TypeVar, Union

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
from strenum import StrEnum

from x10.models.base import X10BaseModel

ApiResponseType = TypeVar("ApiResponseType", bound=Union[int, X10BaseModel, Sequence[X10BaseModel], None])


class ResponseStatus(StrEnum):
    OK = "OK"
    ERROR = "ERROR"


class ResponseErrorModel(X10BaseModel):
    code: int
    message: str
    debug_info: Optional[str] = None


class PaginationModel(X10BaseModel):
    cursor: Optional[int] = None
    count: int


class WrappedApiResponseModel(X10BaseModel, Generic[ApiResponseType]):
    status: ResponseStatus
    data: Optional[ApiResponseType] = None
    error: Optional[ResponseErrorModel] = None
    pagination: Optional[PaginationModel] = None


class StreamDataType(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    BALANCE = "BALANCE"
    DELTA = "DELTA"
    DEPOSIT = "DEPOSIT"
    ORDER = "ORDER"
    POSITION = "POSITION"
    SNAPSHOT = "SNAPSHOT"
    TRADE = "TRADE"
    TRANSFER = "TRANSFER"
    WITHDRAWAL = "WITHDRAWAL"

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(lambda v: v if v in cls._value2member_map_ else cls.UNKNOWN)


class WrappedStreamResponseModel(X10BaseModel, Generic[ApiResponseType]):
    type: Optional[StreamDataType] = None
    data: Optional[ApiResponseType] = None
    error: Optional[str] = None
    ts: int
    seq: int
