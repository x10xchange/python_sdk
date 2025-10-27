import logging
from asyncio import run

from config import ETH_USD_MARKET
from perpetual.accounts import StarkPerpetualAccount
from perpetual.configuration import TESTNET_CONFIG
from perpetual.order_object import OrderTpslTriggerParam, create_order_object
from perpetual.orders import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    TimeInForce,
)
from perpetual.trading_client import PerpetualTradingClient

from examples.init_env import init_env
from examples.utils import get_adjust_price_by_pct

LOGGER = logging.getLogger()
ENDPOINT_CONFIG = TESTNET_CONFIG


async def run_example():
    LOGGER.info("Create limit order with partial TPSL")

    env_config = init_env()
    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )
    trading_client = PerpetualTradingClient(ENDPOINT_CONFIG, stark_account)
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[ETH_USD_MARKET]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size

    order_price = adjust_price_by_pct(market.market_stats.bid_price, -10.0)
    tp_trigger_price = adjust_price_by_pct(order_price, 0.5)
    tp_price = adjust_price_by_pct(order_price, 1.0)
    sl_trigger_price = adjust_price_by_pct(order_price, -0.5)
    sl_price = adjust_price_by_pct(order_price, -1.0)

    LOGGER.info(f"Market: {market}")

    new_order = create_order_object(
        account=stark_account,
        starknet_domain=TESTNET_CONFIG.starknet_domain,
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

    LOGGER.info(f"New order obj: {new_order}")


if __name__ == "__main__":
    run(main=run_example())
