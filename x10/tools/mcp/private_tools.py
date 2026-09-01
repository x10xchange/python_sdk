from typing import Optional

from mcp.server.fastmcp import FastMCP

from x10.tools.mcp.place_order_tool import register_place_order_tool
from x10.tools.mcp.utils import create_private_rest_api_client, serialize_tool_result
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


def register_tools(mcp: FastMCP):
    register_place_order_tool(mcp)

    @mcp.tool()
    async def cancel_order(order_id: int) -> dict:
        """
        Cancel an open order by its ID. Requires authentication env vars.

        Args:
            order_id: The numeric ID of the order to cancel.
        """

        async with create_private_rest_api_client() as client:
            result = await client.orders.cancel_order(order_id=order_id)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def mass_cancel_orders(
        order_ids: Optional[list[int]] = None,
        external_order_ids: Optional[list[str]] = None,
        markets: Optional[list[str]] = None,
        cancel_all: bool = False,
    ) -> dict:
        """
        Cancel multiple open orders at once. Requires authentication env vars.

        Args:
            order_ids: List of numeric order IDs to cancel.
            external_order_ids: List of client-assigned order IDs to cancel.
            markets: List of market names to cancel all orders in, e.g. ["BTC-USD"].
            cancel_all: If True, cancel all open orders regardless of other filters.
        """

        async with create_private_rest_api_client() as client:
            result = await client.orders.mass_cancel(
                order_ids=order_ids,
                external_order_ids=external_order_ids,
                markets=markets,
                cancel_all=cancel_all,
            )
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_balance() -> dict:
        """
        Get account balance. Requires authentication env vars.
        """

        async with create_private_rest_api_client() as client:
            result = await client.account.get_balance()
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_positions(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get open positions. Requires authentication env vars.

        Args:
            market_names: Optional list of market names to filter.
        """

        async with create_private_rest_api_client() as client:
            result = await client.account.get_positions(market_names=market_names)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_open_orders(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get open orders. Requires authentication env vars.

        Args:
            market_names: Optional list of market names to filter.
        """

        async with create_private_rest_api_client() as client:
            result = await client.account.get_open_orders(market_names=market_names)
            return serialize_tool_result(result.data)
