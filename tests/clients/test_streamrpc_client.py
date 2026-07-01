import asyncio
import json

import pytest
import websockets
from hamcrest import assert_that, equal_to
from websockets import WebSocketServer


def get_url_from_server(server: WebSocketServer):
    host, port = server.sockets[0].getsockname()  # type: ignore[index]
    return f"ws://{host}:{port}"


@pytest.mark.asyncio
async def test_candle_stream():
    from tests.fixtures.candle import create_candle_stream_rpc_message
    from x10.clients.streamrpc.streamrpc_client import StreamRpcClient
    from x10.clients.streamrpc.subscription_params import CandlesParams

    message_model = create_candle_stream_rpc_message()
    received_messages: asyncio.Queue = asyncio.Queue()

    async def subscription_handler(msg):
        await received_messages.put(msg)

    async def mock_server(websocket):
        subscribe_msg_raw = await websocket.recv()
        subscribe_msg = json.loads(subscribe_msg_raw)

        assert_that(subscribe_msg["method"], equal_to("subscribe"))

        await websocket.send(
            json.dumps(
                {
                    "id": subscribe_msg["id"],
                    "result": {"subscription": message_model.subscription},
                }
            )
        )

        await websocket.send(json.dumps(message_model.to_api_request_json()))

        unsubscribe_msg_raw = await websocket.recv()
        unsubscribe_msg = json.loads(unsubscribe_msg_raw)

        assert_that(unsubscribe_msg["method"], equal_to("unsubscribe"))

        await websocket.send(
            json.dumps(
                {
                    "id": unsubscribe_msg["id"],
                    "result": {"method": "unsubscribe", "status": "OK"},
                }
            )
        )

    async with websockets.serve(mock_server, "127.0.0.1", 0) as server:
        client = StreamRpcClient(api_url=get_url_from_server(server))
        await client.connect()

        subscription_params = CandlesParams(candle_type="last", market="BTC-USD", interval="PT1M")
        subscription_id = await client.subscribe(params=subscription_params, handler=subscription_handler)

        msg = await asyncio.wait_for(received_messages.get(), timeout=5)

        await client.unsubscribe(topic_id=subscription_id)
        await client.close()

    assert_that(
        msg.to_api_request_json(),
        equal_to(
            {
                "type": "CANDLES",
                "data": [
                    {"o": "3458.64", "l": "3399.07", "h": "3476.89", "c": "3414.85", "v": "3.938", "T": 1721106000000}
                ],
                "error": None,
                "ts": 1721283121979,
                "seq": 1,
                "subscription": "candles.last.BTC-USD.PT1M",
            }
        ),
    )
