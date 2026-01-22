from types import TracebackType
from typing import AsyncIterator, Generic, Optional, Type, TypeVar, Union

import websockets
from websockets import WebSocketClientProtocol

from x10.config import USER_AGENT
from x10.utils.http import RequestHeader
from x10.utils.log import get_logger
from x10.utils.model import X10BaseModel

LOGGER = get_logger(__name__)

StreamMsgResponseType = TypeVar("StreamMsgResponseType", bound=X10BaseModel)

# Check websockets version for API compatibility
_WS_VERSION = tuple(int(x) for x in websockets.__version__.split(".")[:2])
_WS_14_PLUS = _WS_VERSION >= (14, 0)

# Import the correct connection type based on version
if _WS_14_PLUS:
    from websockets.asyncio.client import ClientConnection as WebSocketConnection
else:
    WebSocketConnection = WebSocketClientProtocol


def _is_ws_closed(ws: Union[WebSocketClientProtocol, "WebSocketConnection"]) -> bool:
    """Check if websocket connection is closed (compatible with both ws 13 and 14+)."""
    if _WS_14_PLUS:
        # websockets 14+ uses state enum
        try:
            from websockets.protocol import State
            return ws.state == State.CLOSED
        except (ImportError, AttributeError):
            # Fallback: try to check if close() was called
            return getattr(ws, '_closed', False)
    else:
        # websockets 13 and earlier use .closed property
        return ws.closed


class PerpetualStreamConnection(Generic[StreamMsgResponseType]):
    __stream_url: str
    __msg_model_class: Type[StreamMsgResponseType]
    __api_key: Optional[str]
    __msgs_count: int
    __websocket: Optional[WebSocketClientProtocol]

    def __init__(
        self,
        stream_url: str,
        msg_model_class: Type[StreamMsgResponseType],
        api_key: Optional[str],
    ):
        super().__init__()

        self.__stream_url = stream_url
        self.__msg_model_class = msg_model_class
        self.__api_key = api_key
        self.__msgs_count = 0
        self.__websocket = None

    async def send(self, data):
        assert self.__websocket is not None
        await self.__websocket.send(data)

    async def recv(self) -> StreamMsgResponseType:
        assert self.__websocket is not None
        return await self.__receive()

    async def close(self):
        assert self.__websocket is not None
        if not _is_ws_closed(self.__websocket):
            await self.__websocket.close()
        LOGGER.debug("Stream closed: %s", self.__stream_url)

    @property
    def msgs_count(self):
        return self.__msgs_count

    @property
    def closed(self):
        assert self.__websocket is not None
        return _is_ws_closed(self.__websocket)

    def __aiter__(self) -> AsyncIterator[StreamMsgResponseType]:
        return self

    async def __anext__(self) -> StreamMsgResponseType:
        assert self.__websocket is not None

        if _is_ws_closed(self.__websocket):
            raise StopAsyncIteration
        try:
            return await self.__receive()
        except websockets.ConnectionClosed:
            raise StopAsyncIteration from None

    async def __receive(self) -> StreamMsgResponseType:
        assert self.__websocket is not None

        data = await self.__websocket.recv()
        self.__msgs_count += 1

        return self.__msg_model_class.model_validate_json(data)

    def __await__(self):
        return self.__await_impl__().__await__()

    async def __aenter__(self):
        # Calls `self.__await__()` implicitly
        return await self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ):
        await self.close()

    async def __await_impl__(self):
        headers: dict[str, str] = {
            RequestHeader.USER_AGENT: USER_AGENT,
        }

        if self.__api_key is not None:
            headers[RequestHeader.API_KEY] = self.__api_key

        # websockets 14+ renamed extra_headers to additional_headers
        ws_version = tuple(int(x) for x in websockets.__version__.split(".")[:2])
        if ws_version >= (14, 0):
            self.__websocket = await websockets.connect(self.__stream_url, additional_headers=headers)
        else:
            self.__websocket = await websockets.connect(self.__stream_url, extra_headers=headers)

        LOGGER.debug("Connected to stream: %s", self.__stream_url)

        return self
