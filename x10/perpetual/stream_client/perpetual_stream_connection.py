from types import TracebackType
from typing import AsyncIterator, Generic, Optional, Type, TypeVar

import websockets
from websockets import WebSocketClientProtocol

from x10.config import USER_AGENT
from x10.utils.http import RequestHeader
from x10.utils.log import get_logger
from x10.utils.model import X10BaseModel

LOGGER = get_logger(__name__)

StreamMsgResponseType = TypeVar("StreamMsgResponseType", bound=X10BaseModel)


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
        await self.__websocket.send(data)

    async def recv(self) -> StreamMsgResponseType:
        return await self.__receive()

    async def close(self):
        assert self.__websocket is not None
        assert not self.__websocket.closed

        await self.__websocket.close()

        LOGGER.debug("Stream closed: %s", self.__stream_url)

    @property
    def msgs_count(self):
        return self.__msgs_count

    @property
    def closed(self):
        assert self.__websocket is not None

        return self.__websocket.closed

    def __aiter__(self) -> AsyncIterator[StreamMsgResponseType]:
        return self

    async def __anext__(self) -> StreamMsgResponseType:
        assert self.__websocket is not None

        if self.__websocket.closed:
            raise StopAsyncIteration

        return await self.__receive()

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
        extra_headers = {
            RequestHeader.USER_AGENT.value: USER_AGENT,
        }

        if self.__api_key is not None:
            extra_headers[RequestHeader.API_KEY.value] = self.__api_key

        self.__websocket = await websockets.connect(self.__stream_url, extra_headers=extra_headers)

        LOGGER.debug("Connected to stream: %s", self.__stream_url)

        return self
