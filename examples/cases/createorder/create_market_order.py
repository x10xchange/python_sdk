import logging
from asyncio import run

from examples.utils import create_trading_client
from x10.config import BTC_USD_MARKET, DEFAULT_MARKET_PRICE_SLIPPAGE
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide, OrderType, TimeInForce
from x10.utils.order import get_price_with_slippage

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    trading_client = create_trading_client()
    markets_dict = await trading_client.markets_info.get_markets_dict()
    market_stats = await trading_client.markets_info.get_market_statistics(market_name=MARKET_NAME)

    market = markets_dict[MARKET_NAME]

    order_side = OrderSide.SELL
    order_size = market.trading_config.min_order_size

    best_market_price = market_stats.data.ask_price if order_side == OrderSide.BUY else market_stats.data.bid_price
    order_price = get_price_with_slippage(
        side=order_side,
        price=best_market_price,
        min_price_change=market.trading_config.min_price_change,
        slippage=DEFAULT_MARKET_PRICE_SLIPPAGE,
    )

    LOGGER.info("Creating MARKET order object for market: %s", market.name)

    new_order = create_order_object(
        account=trading_client.stark_account,
        order_type=OrderType.MARKET,
        starknet_domain=trading_client.config.starknet_domain,
        market=market,
        side=order_side,
        amount_of_synthetic=order_size,
        price=order_price,
        time_in_force=TimeInForce.IOC,
        reduce_only=False,
        post_only=False,
    )

    LOGGER.info("Placing order...")

    placed_order = await trading_client.orders.place_order(order=new_order)

    LOGGER.info("Order is placed: %s", placed_order.to_pretty_json())
    LOGGER.warning("Don't forget to reduce/close your position!")


if __name__ == "__main__":
    run(main=run_example())
