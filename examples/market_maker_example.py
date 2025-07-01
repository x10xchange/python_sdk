import asyncio
import math
from decimal import Decimal

from eth_account import Account
from eth_account.signers.local import LocalAccount

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import STARKNET_TESTNET_CONFIG
from x10.perpetual.orders import OrderSide
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

    root_trading_client = PerpetualTradingClient(
        environment_config,
        StarkPerpetualAccount(
            vault=root_account.account.l2_vault,
            private_key=root_account.l2_key_pair.private_hex,
            public_key=root_account.l2_key_pair.public_hex,
            api_key=trading_key,
        ),
    )

    print(f"User 1 v: {root_account.account.l2_vault}")
    print(f"User 1 pub: {root_account.l2_key_pair.public_hex}")
    print(f"User 1 priv: {root_account.l2_key_pair.private_hex}")

    while True:
        markets = await build_markets_cache(root_trading_client)
        try:
            for market in markets.values():
                print(f"Market: {market.name}")
                price_offset = (Decimal(hash(market.name) % 3 - 1) / Decimal(100)) * Decimal(1)
                await root_trading_client.orders.mass_cancel(
                    markets=[market.name],
                )

                if "BTC" not in market.name:  # Example for a specific market
                    print(f"Skipping {market.name} market")
                    continue

                mark_price = market.market_stats.mark_price
                print(f"Mark Price: {mark_price}")
                print(f"price offset: {price_offset}")
                print(f"Min order size: {market.trading_config.min_order_size}")
                base_target = market.trading_config.max_position_value / Decimal(1000)
                sell_prices = [
                    (
                        Decimal(base_target * (i + 1)),
                        round(
                            mark_price + mark_price * Decimal((i * 0.2) / 100.0) + price_offset * mark_price,
                            market.trading_config.price_precision,
                        ),
                    )
                    for i in range(10)
                ]
                buy_prices = [
                    (
                        Decimal(base_target * (i + 1)),
                        round(
                            mark_price - mark_price * Decimal((i * 0.2) / 100.0) + price_offset * mark_price,
                            market.trading_config.price_precision,
                        ),
                    )
                    for i in range(10)
                ]

                for target_value, sell_price in sell_prices:
                    order_size = order_size = market.trading_config.calculate_order_size_from_value(
                        order_value=target_value, order_price=sell_price
                    )
                    print(f"Sell Price: {sell_price}, order size: {order_size}")
                    try:
                        order_response_1 = await root_trading_client.place_order(
                            market_name=market.name,
                            amount_of_synthetic=order_size,
                            price=sell_price,
                            side=OrderSide.SELL,
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                for target_value, buy_price in buy_prices:
                    order_size = market.trading_config.calculate_order_size_from_value(
                        order_value=target_value, order_price=buy_price
                    )
                    print(f"Buy Price: {buy_price}, order size: {order_size}")
                    try:
                        order_response_2 = await root_trading_client.place_order(
                            market_name=market.name,
                            amount_of_synthetic=order_size,
                            price=buy_price,
                            side=OrderSide.BUY,
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                await asyncio.sleep(30)
        except Exception as e:
            print(f"Error: {e}")


asyncio.run(on_board_example())
