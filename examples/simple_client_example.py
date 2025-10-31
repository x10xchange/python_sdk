import asyncio
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide, TimeInForce
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient


async def setup_and_run():
    api_key = "<api>"
    public_key = "<public>"
    private_key = "<private>"
    vault = 100001

    stark_account = StarkPerpetualAccount(
        vault=vault,
        private_key=private_key,
        public_key=public_key,
        api_key=api_key,
    )

    client = await BlockingTradingClient.create(endpoint_config=MAINNET_CONFIG, account=stark_account)
    market = (await client.get_markets())["EDEN-USD"]
    best_ask_condition = asyncio.Condition()
    slippage = Decimal("0.0005")

    async def best_ask_initialised(best_ask):
        async with best_ask_condition:
            best_ask_condition.notify_all()

    orderbook = await OrderBook.create(
        MAINNET_CONFIG,
        market_name=market.name,
        start=True,
        best_ask_change_callback=best_ask_initialised,
        best_bid_change_callback=None,
    )

    async with best_ask_condition:
        await best_ask_condition.wait()

    best_ask_price = orderbook.best_ask()
    if best_ask_price is None:
        raise ValueError("Best ask price is None after initialization")
    order_price = market.trading_config.round_price(best_ask_price.price * (1 + slippage))
    print(f"Best ask price: {best_ask_price}")
    print(f"Placing market order on {market.name} for {market.trading_config.min_order_size} at {order_price}")

    placed_order = await client.create_and_place_order(
        amount_of_synthetic=market.trading_config.min_order_size * Decimal("10"),
        price=order_price,
        market_name=market.name,
        side=OrderSide.BUY,
        post_only=False,
        time_in_force=TimeInForce.IOC,
    )

    print(f"Placed order result: {placed_order}")
    await client.close()
    await orderbook.close()


if __name__ == "__main__":
    asyncio.run(main=setup_and_run())
