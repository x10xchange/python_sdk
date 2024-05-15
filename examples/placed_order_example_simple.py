import logging
import logging.config
import logging.handlers
from asyncio import run
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orders import OrderSide
from x10.perpetual.trading_client import PerpetualTradingClient

NUM_ORDERS_PER_PRICE_LEVEL = 100
NUM_PRICE_LEVELS = 80

API_KEY = "<api_key>"
PRIVATE_KEY = "<private_key>"
PUBLIC_KEY = "<public_key>"
VAULT_ID = 100001


async def clean_it(trading_client: PerpetualTradingClient):
    logger = logging.getLogger("placed_order_example")
    positions = await trading_client.account.get_positions()
    logger.info("Positions: %s", positions.to_pretty_json())
    balance = await trading_client.account.get_balance()
    logger.info("Balance: %s", balance.to_pretty_json())
    open_orders = await trading_client.account.get_open_orders()
    await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])


async def setup_and_run():
    stark_account = StarkPerpetualAccount(
        vault=VAULT_ID,
        private_key=PRIVATE_KEY,
        public_key=PUBLIC_KEY,
        api_key=API_KEY,
    )
    trading_client = PerpetualTradingClient.create(TESTNET_CONFIG, stark_account)
    placed_order = await trading_client.place_order(
        market_name="BTC-USD",
        amount_of_synthetic=Decimal("1"),
        price=Decimal("63000.1"),
        side=OrderSide.SELL,
    )

    await trading_client.orders.cancel_order(order_id=placed_order.id)
    print(placed_order)
    await clean_it(trading_client)


if __name__ == "__main__":
    run(main=setup_and_run())
