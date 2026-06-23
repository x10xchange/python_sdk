import asyncio
from decimal import Decimal
from typing import Optional

from mcp.server import FastMCP

from x10.clients.rest import RestApiClient
from x10.clients.stream import StreamClient
from x10.config import get_config_by_name
from x10.core.env_config import EnvConfig
from x10.core.stark_account import StarkPerpetualAccount
from x10.errors import ValidationError
from x10.models.order import OrderSide, OrderType, SelfTradeProtectionLevel, TimeInForce
from x10.models.orderbook import OrderbookQuantityModel
from x10.signing.order_object import create_order_object
from x10.tools.mcp.utils import serialize_tool_result
from x10.utils.log import get_logger
from x10.utils.order import get_price_with_slippage

LOGGER = get_logger(__name__)


def _create_public_stream_client() -> StreamClient:
    env_config = EnvConfig.parse()
    client_config = get_config_by_name(env_config.client_config_name)

    return StreamClient(api_url=client_config.endpoints.stream_url, close_timeout=1)


def _create_private_rest_api_client() -> RestApiClient:
    env_config = EnvConfig.parse()
    env_config.validate_private_api_credentials()
    client_config = get_config_by_name(env_config.client_config_name)

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return RestApiClient(client_config, stark_account)


async def _get_top_of_book(market_name: str) -> tuple[OrderbookQuantityModel, OrderbookQuantityModel] | None:
    stream_client = _create_public_stream_client()

    LOGGER.debug("Fetching top of book for %s market", market_name)

    async with stream_client.subscribe_to_orderbooks(market_name, depth=1) as orderbook_stream:
        try:
            msg = await asyncio.wait_for(orderbook_stream.recv(), timeout=1)

            assert (
                len(msg.data.bid) == 1 and len(msg.data.ask) == 1
            ), "Orderbook update does not contain bid or ask data"

            return msg.data.bid[0], msg.data.ask[0]
        except asyncio.TimeoutError:
            LOGGER.warn("Timeout while waiting for orderbook update for %s market", market_name)
        finally:
            await orderbook_stream.close()

    LOGGER.debug("Falling back to snapshot for %s market", market_name)

    async with stream_client.subscribe_to_orderbooks(market_name) as orderbook_stream:
        try:
            msg = await asyncio.wait_for(orderbook_stream.recv(), timeout=1)

            assert (
                len(msg.data.bid) > 0 and len(msg.data.ask) > 0
            ), "Orderbook snapshot does not contain bid or ask data"

            return msg.data.bid[0], msg.data.ask[0]
        except asyncio.TimeoutError:
            LOGGER.warn("Timeout while waiting for orderbook update for %s market", market_name)
        finally:
            await orderbook_stream.close()


def register_tools(mcp: FastMCP):
    @mcp.tool()
    async def place_order(
        market_name: str,
        side: OrderSide,
        amount_of_synthetic: Decimal,
        price: Decimal | None = None,
        order_type: OrderType = OrderType.LIMIT,
        post_only: bool = False,
        time_in_force: TimeInForce = TimeInForce.GTT,
        self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
        external_id: Optional[str] = None,
        reduce_only: bool = False,
    ) -> dict:
        """
        Place a new order. Requires authentication env vars.

        Args:
            market_name: Market identifier, e.g. "BTC-USD".
            side: Order side, one of "BUY" or "SELL".
            amount_of_synthetic: Order quantity in base asset units.
            price: Order price. If not provided for MARKET orders, the best bid/ask price will be used.
            order_type: One of "LIMIT", "MARKET". Defaults to "LIMIT".
            post_only: If True, the order will be rejected if it would trade immediately.
            time_in_force: One of "GTT", "IOC", "FOK". Defaults to "GTT".
            self_trade_protection_level: One of "DISABLED", "ACCOUNT", "CLIENT". Defaults to "ACCOUNT".
            external_id: Optional client-assigned order ID.
            reduce_only: If True, the order will only reduce an existing position.
        """

        async with _create_private_rest_api_client() as client:
            markets = await client.info.get_markets_dict()
            market = markets[market_name]

            # FIXME
            if order_type == OrderType.MARKET and price is None:
                r = await _get_top_of_book(market_name)

                if r is None:
                    raise ValidationError(f"Failed to fetch top of book for {market_name}")

                best_bid, best_ask = r
                price = best_ask.price if side == OrderSide.BUY else best_bid.price

                price = get_price_with_slippage(
                    side=side,
                    price=price,
                    min_price_change=market.trading_config.min_price_change,
                    slippage=client.config.defaults.market_price_slippage,
                )

            order = create_order_object(
                account=client.stark_account,
                market=market,
                order_type=order_type,
                side=side,
                amount_of_synthetic=amount_of_synthetic,
                price=price,
                post_only=post_only,
                time_in_force=time_in_force,
                reduce_only=reduce_only,
                order_external_id=external_id,
                self_trade_protection_level=self_trade_protection_level,
                starknet_domain=client.config.signing.starknet_domain,
            )

            result = await client.orders.place_order(order=order)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def cancel_order(order_id: int) -> dict:
        """
        Cancel an open order by its ID. Requires authentication env vars.

        Args:
            order_id: The numeric ID of the order to cancel.
        """

        async with _create_private_rest_api_client() as client:
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

        async with _create_private_rest_api_client() as client:
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

        async with _create_private_rest_api_client() as client:
            result = await client.account.get_balance()
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_positions(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get open positions. Requires authentication env vars.

        Args:
            market_names: Optional list of market names to filter.
        """

        async with _create_private_rest_api_client() as client:
            result = await client.account.get_positions(market_names=market_names)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_open_orders(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get open orders. Requires authentication env vars.

        Args:
            market_names: Optional list of market names to filter.
        """

        async with _create_private_rest_api_client() as client:
            result = await client.account.get_open_orders(market_names=market_names)
            return serialize_tool_result(result.data)
