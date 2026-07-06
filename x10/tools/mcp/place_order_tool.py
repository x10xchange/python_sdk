import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from mcp.server.fastmcp import FastMCP

from x10.clients.rest import RestApiClient
from x10.clients.stream import StreamClient
from x10.config import get_config_by_name
from x10.core.env_config import EnvConfig
from x10.errors import ValidationError
from x10.models.market import MarketModel
from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    OrderType,
    SelfTradeProtectionLevel,
    TimeInForce,
)
from x10.models.orderbook import OrderbookQuantityModel
from x10.signing.order_object import OrderTpslTriggerParam, create_order_object
from x10.tools.mcp.utils import create_private_rest_api_client, serialize_tool_result
from x10.utils.log import get_logger
from x10.utils.order import get_price_with_slippage

LOGGER = get_logger(__name__)


@dataclass(kw_only=True, frozen=True)
class McpOrderTpslTriggerParam:
    """
    MCP specific order trigger parameters.
    ``price`` is required for LIMIT price type only, for MARKET it defaults to
    the trigger price adjusted by the config ``market_price_slippage``.
    """

    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    price: Optional[Decimal] = None
    price_type: OrderPriceType = OrderPriceType.MARKET

    def to_trigger_param(
        self, *, close_side: OrderSide, min_price_change: Decimal, slippage: Decimal
    ) -> OrderTpslTriggerParam:
        price = self.price

        if not price:
            if self.price_type != OrderPriceType.MARKET:
                raise ValidationError("TPSL price is required for non-MARKET orders")

            price = get_price_with_slippage(
                side=close_side,
                price=self.trigger_price,
                min_price_change=min_price_change,
                slippage=slippage,
            )

        return OrderTpslTriggerParam(
            trigger_price=self.trigger_price,
            trigger_price_type=self.trigger_price_type,
            price=price,
            price_type=self.price_type,
        )


def _create_public_stream_client() -> StreamClient:
    env_config = EnvConfig.parse()
    client_config = get_config_by_name(env_config.client_config_name)

    return StreamClient(api_url=client_config.endpoints.stream_url, close_timeout=1)


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

    return None


async def _get_order_price(
    *, client: RestApiClient, market: MarketModel, side: OrderSide, price: Decimal | None
) -> Decimal:
    if price is not None:
        return price

    best_bid_and_ask = await _get_top_of_book(market.name)

    if best_bid_and_ask is None:
        raise ValidationError(f"Failed to fetch top of book for {market.name}")

    best_bid, best_ask = best_bid_and_ask

    return get_price_with_slippage(
        side=side,
        price=best_ask.price if side == OrderSide.BUY else best_bid.price,
        min_price_change=market.trading_config.min_price_change,
        slippage=client.config.defaults.market_price_slippage,
    )


def register_place_order_tool(mcp: FastMCP):
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
        tp_sl_type: Optional[OrderTpslType] = None,
        take_profit: Optional[McpOrderTpslTriggerParam] = None,
        stop_loss: Optional[McpOrderTpslTriggerParam] = None,
    ) -> dict:
        """
        Place a new order. Requires authentication env vars.

        Args:
            market_name: Market name, e.g. "BTC-USD".
            side: Order side, one of "BUY" or "SELL".
            amount_of_synthetic: Order quantity in base asset units.
            price: Order price. If not provided for MARKET orders, the best bid/ask price will be used.
            order_type: One of "LIMIT", "MARKET". Defaults to "LIMIT".
            post_only: If True, the order will be rejected if it would trade immediately.
            time_in_force: One of "GTT", "IOC", "FOK". Defaults to "GTT".
            self_trade_protection_level: One of "DISABLED", "ACCOUNT", "CLIENT". Defaults to "ACCOUNT".
            external_id: Optional client-assigned order ID.
            reduce_only: If True, the order will only reduce an existing position.
            tp_sl_type: One of "ORDER" (TP/SL applies to this order's quantity) or "POSITION"
                (TP/SL applies to the entire position). Required if take_profit or stop_loss is provided.
            take_profit: Take-profit trigger with fields: trigger_price, trigger_price_type
                ("MARK", "INDEX" or "LAST"), price_type ("MARKET" or "LIMIT", defaults to "MARKET")
                and price (execution price; required for "LIMIT" ``price_type``, for "MARKET" it defaults
                to the trigger price adjusted by the config ``market_price_slippage``).
            stop_loss: Stop-loss trigger, same fields as ``take_profit``.
        """

        if order_type != OrderType.MARKET and not price:
            raise ValidationError("Price is required for non-MARKET orders")

        async with create_private_rest_api_client() as client:
            markets = await client.info.get_markets_dict()
            market = markets[market_name]

            order_price = await _get_order_price(client=client, market=market, side=side, price=price)

            close_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
            min_price_change = market.trading_config.min_price_change
            slippage = client.config.defaults.market_price_slippage

            order = create_order_object(
                account=client.stark_account,
                market=market,
                order_type=order_type,
                side=side,
                amount_of_synthetic=amount_of_synthetic,
                price=order_price,
                post_only=post_only,
                time_in_force=time_in_force,
                reduce_only=reduce_only,
                order_external_id=external_id,
                self_trade_protection_level=self_trade_protection_level,
                starknet_domain=client.config.signing.starknet_domain,
                tp_sl_type=tp_sl_type,
                take_profit=take_profit.to_trigger_param(
                    close_side=close_side, min_price_change=min_price_change, slippage=slippage
                )
                if take_profit
                else None,
                stop_loss=stop_loss.to_trigger_param(
                    close_side=close_side, min_price_change=min_price_change, slippage=slippage
                )
                if stop_loss
                else None,
            )

            result = await client.orders.place_order(order=order)
            return serialize_tool_result(result.data)
