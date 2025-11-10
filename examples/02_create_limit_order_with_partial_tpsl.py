import logging
from asyncio import run

from examples.init_env import init_env
from examples.utils import find_order_and_cancel, get_adjust_price_by_pct
from x10.config import ETH_USD_MARKET
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.order_object import OrderTpslTriggerParam, create_order_object
from x10.perpetual.orders import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    TimeInForce,
)
from x10.perpetual.trading_client import PerpetualTradingClient

LOGGER = logging.getLogger()
MARKET_NAME = ETH_USD_MARKET
ENDPOINT_CONFIG = MAINNET_CONFIG


async def run_example():
    env_config = init_env()
    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )
    trading_client = PerpetualTradingClient(ENDPOINT_CONFIG, stark_account)
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size

    order_price = adjust_price_by_pct(market.market_stats.bid_price, -10.0)
    tp_trigger_price = adjust_price_by_pct(order_price, 0.5)
    tp_price = adjust_price_by_pct(order_price, 1.0)
    sl_trigger_price = adjust_price_by_pct(order_price, -0.5)
    sl_price = adjust_price_by_pct(order_price, -1.0)

    LOGGER.info("Creating LIMIT order object with TPSL for market: %s", market.name)

    new_order = create_order_object(
        account=stark_account,
        starknet_domain=ENDPOINT_CONFIG.starknet_domain,
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
            price_type=OrderPriceType.LIMIT,
        ),
    )

    LOGGER.info("Placing order...")

    placed_order = await trading_client.orders.place_order(order=new_order)

    LOGGER.info(f"Order is placed: {placed_order.to_pretty_json()}")

    await find_order_and_cancel(trading_client=trading_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
