import pytest
import websockets
from hamcrest import assert_that, equal_to
from websockets import WebSocketServer


def get_url_from_server(server: WebSocketServer):
    host, port = server.sockets[0].getsockname()  # type: ignore[index]
    return f"ws://{host}:{port}"


def serve_message(message):
    async def _serve_message(websocket):
        await websocket.send(message)

    return _serve_message


@pytest.mark.asyncio
async def test_orderbook_stream(create_orderbook_message):
    from x10.perpetual.stream_client import PerpetualStreamClient

    message_model = create_orderbook_message()

    async with websockets.serve(serve_message(message_model.model_dump_json()), "127.0.0.1", 0) as server:
        stream_client = PerpetualStreamClient(api_url=get_url_from_server(server))
        stream = await stream_client.subscribe_to_orderbooks()
        msg = await stream.recv()
        await stream.close()

        assert_that(
            msg.to_api_request_json(),
            equal_to(
                {
                    "type": "SNAPSHOT",
                    "data": {
                        "m": message_model.data.market,
                        "b": [{"q": "0.008", "p": "43547.00"}, {"q": "0.007000", "p": "43548.00"}],
                        "a": [{"q": "0.008", "p": "43546.00"}],
                    },
                    "error": None,
                    "ts": 1704798222748,
                    "seq": 570,
                }
            ),
        )
