import logging.handlers
from asyncio import run

from examples.utils import create_rest_client, init_env

LOGGER = logging.getLogger()

PAGE_LIMIT = 100


async def run_example():
    init_env()
    rest_client = create_rest_client()

    LOGGER.info("Fetching builder trades (limit=%s)...", PAGE_LIMIT)

    response = await rest_client.builder.get_trades(limit=PAGE_LIMIT)
    trades = response.data or []

    LOGGER.info("Fetched %s trade(s)", len(trades))

    for trade in trades:
        LOGGER.info("Trade: %s", trade.to_pretty_json())

    # Fetch the next page using the cursor returned in the pagination block.
    if response.pagination and response.pagination.cursor:
        next_cursor = response.pagination.cursor

        LOGGER.info("Fetching next page (cursor=%s)...", next_cursor)

        next_response = await rest_client.builder.get_trades(cursor=next_cursor, limit=PAGE_LIMIT)

        LOGGER.info("Fetched %s trade(s) on the next page", len(next_response.data or []))

    await rest_client.close()


if __name__ == "__main__":
    run(main=run_example())
