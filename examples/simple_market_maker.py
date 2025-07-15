import asyncio
import math
import random
import traceback
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import List, Tuple

from eth_account import Account
from eth_account.signers.local import LocalAccount

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import STARKNET_TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient
from x10.perpetual.user_client.user_client import UserClient


async def build_markets_cache(trading_client: PerpetualTradingClient):
    markets = await trading_client.markets_info.get_markets()
    assert markets.data is not None
    return {m.name: m for m in markets.data}


# flake8: noqa
async def on_board_example():
    environment_config = STARKNET_TESTNET_CONFIG
    eth_account_1: LocalAccount = Account.from_key("<YOUR_ETH_PRIVATE_KEY>")
    onboarding_client = UserClient(endpoint_config=environment_config, l1_private_key=eth_account_1.key.hex)
    root_account = await onboarding_client.onboard()
    trading_key = await onboarding_client.create_account_api_key(root_account.account, "trading_key")

    root_trading_client = await BlockingTradingClient.create(
        environment_config,
        StarkPerpetualAccount(
            vault=root_account.account.l2_vault,
            private_key=root_account.l2_key_pair.private_hex,
            public_key=root_account.l2_key_pair.public_hex,
            api_key=trading_key,
        ),
    )

    print(f"User vault: {root_account.account.l2_vault}")
    print(f"User pub: {root_account.l2_key_pair.public_hex}")
    print(f"User priv: {root_account.l2_key_pair.private_hex}")

    available_markets = await root_trading_client.get_markets()
    target_order_amount_usd = Decimal("50")
    market = available_markets["BTC-USD"]
    await root_trading_client.mass_cancel(markets=[market.name])
    buy_orders_infoz: List[Tuple[str, Decimal] | None] = [None, None, None]
    sell_order_infoz: List[Tuple[str, Decimal] | None] = [None, None, None]

    pending_sell_job: asyncio.Future[list[BaseException | None]] | None = None
    pending_buy_job: asyncio.Future[list[BaseException | None]] | None = None

    def update_sell_orders(best_ask: Decimal | None):
        print(f"Best ask: {best_ask}")
        nonlocal pending_sell_job
        if pending_sell_job and not pending_sell_job.done():
            print("Pending sell job is still running, skipping update.")
            return
        tasks = [
            asyncio.create_task(place_order(best_ask, idx, OrderSide.SELL)) for idx in range(len(sell_order_infoz))
        ]
        pending_sell_job = asyncio.gather(*tasks, return_exceptions=True)

    def update_buy_orders(best_bid: Decimal | None):
        print(f"Best bid: {best_bid}")
        nonlocal pending_buy_job
        if pending_buy_job and not pending_buy_job.done():
            print("Pending buy job is still running, skipping update.")
            return
        tasks = [asyncio.create_task(place_order(best_bid, idx, OrderSide.BUY)) for idx in range(len(buy_orders_infoz))]
        pending_buy_job = asyncio.gather(*tasks, return_exceptions=True)

    async def place_order(best_price: Decimal | None, idx: int, side: OrderSide):
        order_holders = sell_order_infoz if side == OrderSide.SELL else buy_orders_infoz
        try:
            previous_order_info = order_holders[idx]
            if previous_order_info is not None:
                previous_order_id, previous_order_price = previous_order_info
            else:
                previous_order_id, previous_order_price = None, None
            print(f"Previous order ID: {previous_order_id}, Price: {previous_order_price}")

            if previous_order_id and previous_order_price and previous_order_price == best_price:
                print(f"Order at index {idx} with price {previous_order_price} is at top of the book, cancelling.")
                await root_trading_client.cancel_order(previous_order_id)
                order_holders[idx] = None
                previous_order_id = None

            if best_price is None:
                print(f"No best price available for index {idx}, skipping {side} order placement.")
                return
            new_external_id = (
                f"mm_{side}_order_{idx}_{random.randint(1,10000000000000000000000000000000000000000000000000000000000)}"
            )

            adjustment_direction = Decimal(1 if side == OrderSide.SELL else -1)

            adjusted_price = market.trading_config.round_price(
                best_price * (Decimal(1) + (adjustment_direction * (Decimal(1) + Decimal(idx)) / Decimal(400))),
                ROUND_CEILING,
            )
            print(f"Placing {side} order at {adjusted_price} for index {idx}")
            synthetic_amount = market.trading_config.calculate_order_size_from_value(
                target_order_amount_usd, adjusted_price
            )
            place_response = await root_trading_client.create_and_place_order(
                market_name=market.name,
                amount_of_synthetic=synthetic_amount,
                price=adjusted_price,
                side=side,
                post_only=True,
                previous_order_external_id=previous_order_id,
                external_id=new_external_id,
            )
            order_holders[idx] = (new_external_id, adjusted_price)
            print(f"Placed sell order at {adjusted_price} with ID {place_response.external_id}")
        except Exception as e:
            print(traceback.format_exc())

    order_book = await OrderBook.create(
        STARKNET_TESTNET_CONFIG,
        market_name="BTC-USD",
        start=True,
        best_ask_change_callback=lambda best_ask: update_buy_orders(best_ask.price if best_ask else None),
        best_bid_change_callback=lambda best_bid: update_sell_orders(best_bid.price if best_bid else None),
    )

    while True:
        await asyncio.sleep(1)


asyncio.run(on_board_example())
