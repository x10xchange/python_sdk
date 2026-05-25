import logging
from asyncio import run
from decimal import Decimal

from examples.utils import (
    BTC_USD_MARKET,
    create_rest_client,
    find_order_and_cancel,
    get_adjust_price_by_pct,
)
from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    OrderType,
    TimeInForce,
)
from x10.signing.order_object import OrderTpslTriggerParam, create_order_object

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    rest_client = create_rest_client()
    markets_dict = await rest_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    last_price = market.market_stats.last_price
    tp_trigger_price = adjust_price_by_pct(last_price, -5)
    tp_price = adjust_price_by_pct(tp_trigger_price, -5)
    sl_trigger_price = adjust_price_by_pct(last_price, 5)
    sl_price = adjust_price_by_pct(sl_trigger_price, 5)

    LOGGER.info("Creating entire position TPSL order object for market: %s", market.name)

    new_order = create_order_object(
        account=rest_client.stark_account,
        starknet_domain=rest_client.config.signing.starknet_domain,
        market=market,
        order_type=OrderType.TPSL,
        side=OrderSide.SELL,
        amount_of_synthetic=Decimal(0),
        price=Decimal(0),
        time_in_force=TimeInForce.GTT,
        reduce_only=True,
        post_only=False,
        tp_sl_type=OrderTpslType.POSITION,
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
            price_type=OrderPriceType.LIMIT,
        ),
    )

    LOGGER.info("Placing order...")

    placed_order = await rest_client.orders.place_order(order=new_order)

    LOGGER.info(f"Order is placed: {placed_order.to_pretty_json()}")

    await find_order_and_cancel(rest_client=rest_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
