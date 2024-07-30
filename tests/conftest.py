import pytest


@pytest.fixture
def create_accounts():
    from tests.fixtures.accounts import create_accounts as _create_accounts

    return _create_accounts


@pytest.fixture
def create_trading_account():
    from tests.fixtures.accounts import (
        create_trading_account as _create_trading_account,
    )

    return _create_trading_account


@pytest.fixture
def btc_usd_market_json_data():
    from tests.fixtures.markets import get_btc_usd_market_json_data

    return get_btc_usd_market_json_data()


@pytest.fixture
def create_btc_usd_market(btc_usd_market_json_data):
    from tests.fixtures.markets import create_btc_usd_market as _create_btc_usd_market

    return lambda: _create_btc_usd_market(btc_usd_market_json_data)


@pytest.fixture
def create_orderbook_message():
    from tests.fixtures.orderbook import (
        create_orderbook_message as _create_orderbook_message,
    )

    return _create_orderbook_message


@pytest.fixture
def create_account_update_trade_message():
    from tests.fixtures.accounts import (
        create_account_update_trade_message as _create_account_update_trade_message,
    )

    return _create_account_update_trade_message


@pytest.fixture
def create_account_update_unknown_message():
    from tests.fixtures.accounts import (
        create_account_update_unknown_message as _create_account_update_unknown_message,
    )

    return _create_account_update_unknown_message


@pytest.fixture
def create_asset_operations():
    from tests.fixtures.assets import (
        create_asset_operations as _create_asset_operations,
    )

    return _create_asset_operations
