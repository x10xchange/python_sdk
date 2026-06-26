from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


class StreamRPCClient:
    """
    X10 WebSocket RPC client.

    Implements the JSON-RPC 2.0 like protocol over a WebSocket connection.
    Supports automatic reconnection and transparent re-subscription after connection loss.

    :param api_url: Full WebSocket URL
    """

    async def connect(self):
        LOGGER.debug("Connecting to %s", self._api_url)
        pass

    async def close(self):
        pass

    async def ping(self):
        pass

    async def list_subscriptions(self):
        pass

    async def subscribe(self):
        pass

    async def unsubscribe(self):
        pass

    def __init__(self, api_url: str):
        self._api_url = api_url

    async def __aenter__(self) -> "StreamRPCClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()
