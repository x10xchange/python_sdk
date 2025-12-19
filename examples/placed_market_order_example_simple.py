import asyncio
import logging
import logging.config
import logging.handlers
import os
import random
from asyncio import run
from decimal import ROUND_DOWN, Decimal

from dotenv import load_dotenv

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide, OrderType, TimeInForce
from x10.perpetual.trading_client import PerpetualTradingClient

load_dotenv()
MARKET_NAME = "BTC-USD"
ORDER_QTY = Decimal("0.0001")

API_KEY = os.getenv("X10_API_KEY")
PUBLIC_KEY = os.getenv("X10_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("X10_PRIVATE_KEY")
VAULT_ID = int(os.environ["X10_VAULT_ID"])


def round_to_step(value: Decimal, step: Decimal) -> Decimal:
    """
    Round a Decimal down to the nearest multiple of `step`.
    This matches typical "tick size" / "min price change" and size step constraints.
    """
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def marketable_price(side: OrderSide, best_bid: Decimal, best_ask: Decimal) -> Decimal:
    """
    Create a marketable price using a fixed offset from best bid/ask.
    Extended requires a price field even for MARKET+IOC.
    """
    if side == OrderSide.BUY:
        return best_ask * (Decimal("1") + Decimal("0.002"))
    return best_bid * (Decimal("1") - Decimal("0.002"))


async def clean_it(trading_client: PerpetualTradingClient):
    logger = logging.getLogger("placed_order_example")
    positions = await trading_client.account.get_positions()
    logger.info("Positions: %s", positions.to_pretty_json())
    balance = await trading_client.account.get_balance()
    logger.info("Balance: %s", balance.to_pretty_json())
    open_orders = await trading_client.account.get_open_orders()
    await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])


async def setup_and_run():
    assert API_KEY is not None
    assert PUBLIC_KEY is not None
    assert PRIVATE_KEY is not None
    assert VAULT_ID is not None

    stark_account = StarkPerpetualAccount(
        vault=VAULT_ID,
        private_key=PRIVATE_KEY,
        public_key=PUBLIC_KEY,
        api_key=API_KEY,
    )
    trading_client = PerpetualTradingClient(
        endpoint_config=TESTNET_CONFIG,
        stark_account=stark_account,
    )
    positions = await trading_client.account.get_positions()
    for position in positions.data:
        print(
            f"market: {position.market} \
            side: {position.side} \
            size: {position.size} \
            mark_price: ${position.mark_price} \
            leverage: {position.leverage}"
        )
        print(f"consumed im: ${round((position.size * position.mark_price) / position.leverage, 2)}")

    await clean_it(trading_client)

    markets = await trading_client.markets_info.get_markets_dict()
    market = markets.get(MARKET_NAME)
    tick_size = market.trading_config.min_price_change
    size_step = market.trading_config.min_order_size_change

    orderbook = await OrderBook.create(endpoint_config=TESTNET_CONFIG, market_name=MARKET_NAME)

    await orderbook.start_orderbook()

    # Place a single MARKET+IOC order (venue requirement) using a marketable price.
    # Note: this can open a real position on the venue. Use tiny size and close manually if needed.
    while True:
        bid = orderbook.best_bid()
        ask = orderbook.best_ask()
        if bid and ask:
            best_bid = bid.price
            best_ask = ask.price
            break
        await asyncio.sleep(0.5)

    side = OrderSide.BUY
    raw_price = marketable_price(side=side, best_bid=best_bid, best_ask=best_ask)
    price = round_to_step(raw_price, tick_size)
    qty = round_to_step(ORDER_QTY, size_step)
    if qty <= 0:
        raise ValueError(f"Order qty rounds to 0 (ORDER_QTY={ORDER_QTY}, step={size_step})")

    external_id = str(random.randint(1, 10**40))
    placed = await trading_client.place_order(
        market_name=MARKET_NAME,
        amount_of_synthetic=qty,
        price=price,
        side=side,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.IOC,
        post_only=False,
        external_id=external_id,
    )
    placed_id = placed.data.id if placed.data is not None else None
    print(
        f"placed: market={MARKET_NAME} side={side.value} qty={qty} price={price} "
        f"tif=IOC type=MARKET external_id={external_id} => id={placed_id}"
    )

    positions = await trading_client.account.get_positions()
    print("positions:", positions.to_pretty_json())


if __name__ == "__main__":
    run(main=setup_and_run())
