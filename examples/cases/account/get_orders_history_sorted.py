import logging.handlers
from asyncio import run

from examples.utils import BTC_USD_MARKET, create_rest_client, init_env
from x10.models.order import OrderSortBy

LOGGER = logging.getLogger()

MARKET_NAME = BTC_USD_MARKET
PAGE_LIMIT = 50


async def run_example():
    init_env()
    rest_client = create_rest_client()

    # Sort by last update time instead of the default (order id).
    LOGGER.info("Fetching order history for %s sorted by %s...", MARKET_NAME, OrderSortBy.UPDATED_AT)

    response = await rest_client.account.get_orders_history(
        market_names=[MARKET_NAME],
        limit=PAGE_LIMIT,
        sort=OrderSortBy.UPDATED_AT,
    )
    orders = response.data or []

    LOGGER.info("Fetched %s order(s)", len(orders))

    for order in orders:
        LOGGER.info("Order: %s", order.to_pretty_json())

    await rest_client.close()


if __name__ == "__main__":
    run(main=run_example())
