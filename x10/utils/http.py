import itertools
import re
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar, Union

import aiohttp
from aiohttp import ClientResponse, ClientTimeout
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from x10.config import DEFAULT_REQUEST_TIMEOUT_SECONDS, USER_AGENT
from x10.errors import X10Error
from x10.utils.log import get_logger
from x10.utils.model import X10BaseModel

LOGGER = get_logger(__name__)
CLIENT_TIMEOUT = ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT_SECONDS)

ApiResponseType = TypeVar("ApiResponseType", bound=Union[int, X10BaseModel, Sequence[X10BaseModel]])


class RateLimitException(X10Error):
    pass


class NotAuthorizedException(X10Error):
    pass


class RequestHeader(Enum):
    ACCEPT = "Accept"
    API_KEY = "X-Api-Key"
    CONTENT_TYPE = "Content-Type"
    USER_AGENT = "User-Agent"


class ResponseStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"


class ResponseError(X10BaseModel):
    code: int
    message: str


class Pagination(X10BaseModel):
    cursor: Optional[int] = None
    count: int


class WrappedApiResponse(X10BaseModel, Generic[ApiResponseType]):
    status: ResponseStatus
    data: Optional[ApiResponseType] = None
    error: Optional[ResponseError] = None
    pagination: Optional[Pagination] = None


class StreamDataType(Enum):
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


class WrappedStreamResponse(X10BaseModel, Generic[ApiResponseType]):
    type: Optional[StreamDataType] = None
    data: Optional[ApiResponseType] = None
    error: Optional[str] = None
    ts: int
    seq: int


def parse_response_to_model(
    response_text: str, model_class: Type[ApiResponseType]
) -> WrappedApiResponse[ApiResponseType]:
    # Read this to get more context re the type ignore:
    # https://github.com/python/mypy/issues/13619
    return WrappedApiResponse[model_class].model_validate_json(response_text)  # type: ignore[valid-type]


def get_url(template: str, *, query: Optional[Dict[str, str | List[str]]] = None, **path_params):
    def replace_path_param(match: re.Match[str]):
        matched_value = match.group(1)
        is_param_optional = matched_value.endswith("?")
        param_key = matched_value[:-1] if is_param_optional else matched_value
        param_value = path_params.get(param_key, "") if is_param_optional else path_params[param_key]

        return str(param_value) if param_value is not None else ""

    def serialize_query_param(param_key: str, param_value: Union[str, List[str]]):
        if isinstance(param_value, list):
            return itertools.chain.from_iterable(
                [serialize_query_param(param_key, item) for item in param_value if item is not None]
            )
        elif isinstance(param_value, Enum):
            return [f"{param_key}={param_value.value}"]
        elif param_value is not None:
            return [f"{param_key}={param_value}"]
        else:
            return []

    template = re.sub(r"<(\??[^<>]+)>", replace_path_param, template)
    template = template.rstrip("/")

    if query:
        query_parts = []

        for key, value in query.items():
            query_parts.extend(serialize_query_param(key, value))

        template += "?" + "&".join(query_parts)

    return template


async def send_get_request(
    session: aiohttp.ClientSession,
    url: str,
    model_class: Type[ApiResponseType],
    *,
    api_key: Optional[str] = None,
    request_headers: Optional[Dict[str, str]] = None,
    response_code_to_exception: Optional[Dict[int, Type[Exception]]] = None,
) -> WrappedApiResponse[ApiResponseType]:
    headers = __get_headers(api_key=api_key, request_headers=request_headers)
    LOGGER.debug("Sending GET %s", url)
    async with session.get(url, headers=headers) as response:
        response_text = await response.text()
        handle_known_errors(url, response_code_to_exception, response, response_text)
        return parse_response_to_model(response_text, model_class)


async def send_post_request(
    session: aiohttp.ClientSession,
    url: str,
    model_class: Type[ApiResponseType],
    *,
    json: Any = None,
    api_key: Optional[str] = None,
    request_headers: Optional[Dict[str, str]] = None,
    response_code_to_exception: Optional[Dict[int, Type[Exception]]] = None,
) -> WrappedApiResponse[ApiResponseType]:
    headers = __get_headers(api_key=api_key, request_headers=request_headers)
    LOGGER.debug("Sending POST %s, headers=%s", url, headers)
    async with session.post(url, json=json, headers=headers) as response:
        response_text = await response.text()
        handle_known_errors(url, response_code_to_exception, response, response_text)
        response_model = parse_response_to_model(response_text, model_class)
        if (response_model.status != ResponseStatus.OK.value) or (response_model.error is not None):
            LOGGER.error("Error response from POST %s: %s", url, response_model.error)
            raise ValueError(f"Error response from POST {url}: {response_model.error}")
        return response_model


async def send_patch_request(
    session: aiohttp.ClientSession,
    url: str,
    model_class: Type[ApiResponseType],
    *,
    json: Any = None,
    api_key: Optional[str] = None,
    request_headers: Optional[Dict[str, str]] = None,
    response_code_to_exception: Optional[Dict[int, Type[Exception]]] = None,
) -> WrappedApiResponse[ApiResponseType]:
    headers = __get_headers(api_key=api_key, request_headers=request_headers)
    LOGGER.debug("Sending PATCH %s, headers=%s, data=%s", url, headers, json)
    async with session.patch(url, json=json, headers=headers) as response:
        response_text = await response.text()
        if response_text == "":
            LOGGER.error("Empty HTTP %s response from PATCH %s", response.status, url)
            response_text = '{"status": "OK"}'
        handle_known_errors(url, response_code_to_exception, response, response_text)
        return parse_response_to_model(response_text, model_class)


async def send_delete_request(
    session: aiohttp.ClientSession,
    url: str,
    model_class: Type[ApiResponseType],
    *,
    api_key: Optional[str] = None,
    request_headers: Optional[Dict[str, str]] = None,
    response_code_to_exception: Optional[Dict[int, Type[Exception]]] = None,
):
    headers = __get_headers(api_key=api_key, request_headers=request_headers)
    LOGGER.debug("Sending DELETE %s, headers=%s", url, headers)
    async with session.delete(url, headers=headers) as response:
        response_text = await response.text()
        handle_known_errors(url, response_code_to_exception, response, response_text)
        return parse_response_to_model(response_text, model_class)


def handle_known_errors(
    url, response_code_handler: Optional[Dict[int, Type[Exception]]], response: ClientResponse, response_text: str
):
    if response.status == 401:
        LOGGER.error("Unauthorized response from POST %s: %s", url, response_text)
        raise NotAuthorizedException(f"Unauthorized response from POST {url}: {response_text}")

    if response.status == 429:
        LOGGER.error("Rate limited response from POST %s: %s", url, response_text)
        raise RateLimitException(f"Rate limited response from POST {url}: {response}")

    if response_code_handler and response.status in response_code_handler:
        raise response_code_handler[response.status](response_text)

    if response.status > 299:
        LOGGER.error("Error response from POST %s: %s", url, response_text)
        raise ValueError(f"Error response from POST {url}: code {response.status} - {response_text}")


def __get_headers(*, api_key: Optional[str] = None, request_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        RequestHeader.ACCEPT.value: "application/json",
        RequestHeader.CONTENT_TYPE.value: "application/json",
        RequestHeader.USER_AGENT.value: USER_AGENT,
    }

    if api_key:
        headers[RequestHeader.API_KEY.value] = api_key

    if request_headers:
        headers.update(request_headers)

    return headers
