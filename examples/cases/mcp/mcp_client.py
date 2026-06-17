import json
import logging
import os
import sys
from asyncio import run

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from examples.utils import init_env

LOGGER = logging.getLogger()


async def list_available_mcp_tools(session: ClientSession):
    LOGGER.info("--- Available tools ---")

    tools_response = await session.list_tools()
    tool_names = [t.name for t in tools_response.tools]

    LOGGER.info("Tools (%d): %s", len(tool_names), tool_names)


async def list_markets(session: ClientSession):
    LOGGER.info("--- Markets ---")

    markets_result = await session.call_tool("get_markets", {})
    markets_result_as_text = _tool_result_text(markets_result)
    markets_result_as_json = json.loads(markets_result_as_text)

    LOGGER.info("Markets count: %d", len(markets_result_as_json))

    if markets_result_as_json:
        first_market = markets_result_as_json[0]
        LOGGER.info("First market: %s", first_market["name"])


async def run_example():
    init_env()

    server_params = StdioServerParameters(command=sys.executable, args=["-m", "x10.tools.mcp_server"], env=os.environ)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await list_available_mcp_tools(session)
            await list_markets(session)

            # ------------------------------------------------------------------
            # 2. Public tools — market data
            # ------------------------------------------------------------------

            # LOGGER.info("--- get_market_statistics [%s] ---", MARKET_NAME)
            # stats_result = await session.call_tool("get_market_statistics", {"market_name": MARKET_NAME})
            # LOGGER.info("Stats: %s", _pretty(json.loads(_tool_result_text(stats_result))))
            #
            # LOGGER.info("--- get_orderbook_snapshot [%s] ---", MARKET_NAME)
            # ob_result = await session.call_tool("get_orderbook_snapshot", {"market_name": MARKET_NAME})
            # ob = json.loads(_tool_result_text(ob_result))
            # LOGGER.info(
            #     "Orderbook: %d bids, %d asks",
            #     len(ob.get("bid", [])),
            #     len(ob.get("ask", [])),
            # )
            #
            # LOGGER.info("--- get_asset_price [BTC] ---")
            # price_result = await session.call_tool("get_asset_price", {"asset_name": "BTC"})
            # LOGGER.info("BTC price: %s", _tool_result_text(price_result))
            #
            # LOGGER.info("--- get_candles_history [%s] ---", MARKET_NAME)
            # candles_result = await session.call_tool(
            #     "get_candles_history",
            #     {
            #         "market_name": MARKET_NAME,
            #         "candle_type": "trades",
            #         "interval": "PT1H",
            #         "limit": 5,
            #     },
            # )
            # candles = json.loads(_tool_result_text(candles_result))
            # LOGGER.info("Candles returned: %d", len(candles))
            # if candles:
            #     LOGGER.info("Latest candle: %s", _pretty(candles[-1]))
            #
            # # ------------------------------------------------------------------
            # # 3. Authenticated tools — account data (skipped if no credentials)
            # # ------------------------------------------------------------------
            # env = init_env(require_private_api=False)
            # has_credentials = all([env.api_key, env.public_key, env.private_key, env.vault_id])
            #
            # if not has_credentials:
            #     LOGGER.info(
            #         "Skipping authenticated tools — "
            #         "set X10_API_KEY, X10_PUBLIC_KEY, X10_PRIVATE_KEY, X10_VAULT_ID to enable."
            #     )
            #     return
            #
            # LOGGER.info("--- get_balance ---")
            # balance_result = await session.call_tool("get_balance", {})
            # LOGGER.info("Balance: %s", _pretty(json.loads(_tool_result_text(balance_result))))
            #
            # LOGGER.info("--- get_positions ---")
            # positions_result = await session.call_tool("get_positions", {})
            # positions = json.loads(_tool_result_text(positions_result))
            # LOGGER.info("Open positions: %d", len(positions))
            #
            # LOGGER.info("--- get_open_orders ---")
            # orders_result = await session.call_tool("get_open_orders", {})
            # orders = json.loads(_tool_result_text(orders_result))
            # LOGGER.info("Open orders: %d", len(orders))


def _pretty(obj) -> str:
    return json.dumps(obj, indent=2, default=str)


def _tool_result_text(result) -> str:
    texts = [content.text for content in result.content if hasattr(content, "text")]
    if not texts:
        return str(result.content)
    # FIXME: ???
    if len(texts) == 1:
        return texts[0]
    # Multiple blocks — each may be a JSON-serialised item; reconstruct as array.
    items = []
    for t in texts:
        try:
            items.append(json.loads(t))
        except json.JSONDecodeError:
            items.append(t)
    return json.dumps(items, default=str)


if __name__ == "__main__":
    run(main=run_example())
