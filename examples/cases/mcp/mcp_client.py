import asyncio
import json
import logging
import os
import sys

import aiohttp
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from examples.utils import BTC_USD_MARKET, init_env

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"


async def list_available_mcp_tools(session: ClientSession):
    LOGGER.info("--- Available tools ---")

    result = await session.list_tools()
    tool_names = [t.name for t in result.tools]

    LOGGER.info("Tools (%d): %s", len(tool_names), tool_names)


async def call_get_markets(session: ClientSession):
    LOGGER.info("--- Markets ---")

    result = await session.call_tool("get_markets", {})
    result_as_text = _tool_result_as_text(result)
    result_as_json = json.loads(result_as_text)

    LOGGER.info("Markets count: %d", len(result_as_json))

    if result_as_json:
        first_market = result_as_json[0]
        LOGGER.info("First market: %s", first_market["name"])


async def call_get_market_statistics(session: ClientSession, market_name: str):
    LOGGER.info("--- Market statistics for %s ---", market_name)

    result = await session.call_tool("get_market_statistics", {"market_name": market_name})
    result_as_text = _tool_result_as_text(result)
    result_as_json = json.loads(result_as_text)

    LOGGER.info("Last price: %s", result_as_json["lastPrice"])


async def call_get_orderbook_snapshot(session: ClientSession, market_name: str):
    LOGGER.info("--- Orderbook snapshot for %s ---", market_name)

    result = await session.call_tool("get_orderbook_snapshot", {"market_name": market_name})
    result_as_text = _tool_result_as_text(result)
    result_as_json = json.loads(result_as_text)

    LOGGER.info(
        "Orderbook: %d bids, %d asks",
        len(result_as_json.get("b", [])),
        len(result_as_json.get("a", [])),
    )


async def call_get_candles_history(session: ClientSession, market_name: str):
    LOGGER.info("--- Candles history for %s ---", market_name)

    result = await session.call_tool(
        "get_candles_history",
        {
            "market_name": market_name,
            "candle_type": "trades",
            "interval": "PT1H",
            "limit": 5,
        },
    )
    result_as_text = _tool_result_as_text(result)
    result_as_json = json.loads(result_as_text)

    LOGGER.info("Candles returned: %d", len(result_as_json))

    if result_as_json:
        LOGGER.info("Latest candle: %s", result_as_json[-1])


async def call_get_balance(session: ClientSession):
    LOGGER.info("--- Balance ---")

    result = await session.call_tool("get_balance", {})
    result_as_text = _tool_result_as_text(result)
    result_as_json = json.loads(result_as_text)

    LOGGER.info("Balance: %s", result_as_json["balance"])


async def call_get_positions(session: ClientSession):
    LOGGER.info("--- Positions ---")

    result = await session.call_tool("get_positions", {})
    result_as_text = _tool_result_as_text(result, force_list=True)
    result_as_json = json.loads(result_as_text)

    LOGGER.info("Positions (%d): %s", len(result_as_json), [p["market"] for p in result_as_json])


async def call_get_open_orders(session: ClientSession):
    LOGGER.info("--- Open orders ---")

    result = await session.call_tool("get_open_orders", {})
    result_as_text = _tool_result_as_text(result, force_list=True)
    result_as_json = json.loads(result_as_text)

    LOGGER.info("Open orders (%d): %s", len(result_as_json), [p["market"] for p in result_as_json])


async def run_example():
    init_env()

    server_proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "x10.tools.mcp.mcp_server",
        env=os.environ,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    try:
        await _wait_for_server(10.0)

        async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                await list_available_mcp_tools(session)

                await call_get_markets(session)
                await call_get_market_statistics(session, MARKET_NAME)
                await call_get_orderbook_snapshot(session, MARKET_NAME)
                await call_get_candles_history(session, MARKET_NAME)

                await call_get_balance(session)
                await call_get_positions(session)
                await call_get_open_orders(session)
    finally:
        server_proc.terminate()
        await server_proc.wait()


async def _wait_for_server(timeout: float):
    deadline = asyncio.get_event_loop().time() + timeout

    async with aiohttp.ClientSession() as client:
        while asyncio.get_event_loop().time() < deadline:
            try:
                await client.get(MCP_SERVER_URL, timeout=aiohttp.ClientTimeout(total=1.0))
                return
            except aiohttp.ClientConnectorError:
                await asyncio.sleep(0.2)

    raise TimeoutError(f"MCP server did not become ready at {MCP_SERVER_URL} within {timeout}s")


def _tool_result_as_text(result, *, force_list=False) -> str:
    texts = [content.text for content in result.content if hasattr(content, "text")]

    if not texts:
        return str(result.content)

    if len(texts) == 1 and not force_list:
        return texts[0]

    items = []

    for text in texts:
        items.append(json.loads(text))

    return json.dumps(items, default=str)


if __name__ == "__main__":
    asyncio.run(run_example())
