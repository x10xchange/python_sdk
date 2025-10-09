import logging
import logging.config
import logging.handlers
import os
from asyncio import run
from decimal import Decimal

from dotenv import load_dotenv

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orders import OrderSide
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.trading_client import PerpetualTradingClient

NUM_PRICE_LEVELS = 1

load_dotenv()

API_KEY = os.getenv("X10_API_KEY")
PUBLIC_KEY = os.getenv("X10_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("X10_PRIVATE_KEY")
VAULT_ID = int(os.environ["X10_VAULT_ID"])


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
        private_key="" if PRIVATE_KEY is None else PRIVATE_KEY,
        public_key="" if PUBLIC_KEY is None else PUBLIC_KEY,
        api_key="" if API_KEY is None else API_KEY,
    )
    trading_client = PerpetualTradingClient(
        endpoint_config=TESTNET_CONFIG,
        stark_account=stark_account,
    )
    builder_id = 2001
    builder_fee = (
        (await trading_client.account.get_fees(market_names=["BTC-USD"], builder_id=builder_id))
        .data[0]
        .builder_fee_rate
    )

    positions = await trading_client.account.get_positions()
    for position in positions.data:
        print(f"consumed im: ${round((position.size * position.mark_price) / position.leverage, 2)}")

    await clean_it(trading_client)

    blocking_client = BlockingTradingClient(
        endpoint_config=TESTNET_CONFIG,
        account=stark_account,
    )

    await blocking_client.create_and_place_order(
        amount_of_synthetic=Decimal("0.1"),
        price=Decimal("122001"),
        market_name="BTC-USD",
        side=OrderSide.BUY,
        post_only=False,
        external_id="0x123",
        builder_id=builder_id,
        builder_fee=builder_fee,
    )


if __name__ == "__main__":
    run(main=setup_and_run())
