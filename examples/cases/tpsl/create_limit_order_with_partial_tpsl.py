import logging
from asyncio import run
from decimal import Decimal

from examples.utils import (
    create_trading_client,
    find_order_and_cancel,
    get_adjust_price_by_pct,
)
from x10.config import BTC_USD_MARKET, DEFAULT_MARKET_PRICE_SLIPPAGE
from x10.perpetual.order_object import OrderTpslTriggerParam, create_order_object
from x10.perpetual.orders import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    TimeInForce,
)

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    trading_client = create_trading_client()
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size

    order_price = adjust_price_by_pct(market.market_stats.bid_price, -10.0)
    tp_trigger_price = adjust_price_by_pct(order_price, 0.5)
    tp_price = adjust_price_by_pct(tp_trigger_price, 0.5)
    sl_trigger_price = adjust_price_by_pct(order_price, -0.5)
    sl_price = adjust_price_by_pct(sl_trigger_price, -DEFAULT_MARKET_PRICE_SLIPPAGE * Decimal("100"))

    LOGGER.info("Creating LIMIT order object with TPSL for market: %s", market.name)

    new_order = create_order_object(
        account=trading_client.stark_account,
        starknet_domain=trading_client.config.starknet_domain,
        market=market,
        side=OrderSide.BUY,
        amount_of_synthetic=order_size,
        price=market.trading_config.round_price(order_price),
        time_in_force=TimeInForce.GTT,
        reduce_only=False,
        post_only=True,
        tp_sl_type=OrderTpslType.ORDER,
        take_profit=OrderTpslTriggerParam(
            trigger_price=tp_trigger_price,
            trigger_price_type=OrderTriggerPriceType.LAST,
            price=tp_price,
            price_type=OrderPriceType.LIMIT,
        ),
        stop_loss=OrderTpslTriggerParam(
            trigger_price=sl_trigger_price,
            trigger_price_type=OrderTriggerPriceType.LAST,
            price=sl_price,
            price_type=OrderPriceType.MARKET,
        ),
    )

    LOGGER.info("Placing order...")

    placed_order = await trading_client.orders.place_order(order=new_order)

    LOGGER.info(f"Order is placed: {placed_order.to_pretty_json()}")

    await find_order_and_cancel(trading_client=trading_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
