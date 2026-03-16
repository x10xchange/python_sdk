"""
Test fixtures for Extended SDK tests.

Provides sample data structures for testing transformers and APIs.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

import pytest

from x10.perpetual.balances import BalanceModel
from x10.perpetual.candles import CandleModel
from x10.perpetual.markets import (
    MarketModel,
    MarketStatsModel,
    TradingConfigModel,
    L2ConfigModel,
    RiskFactorConfig,
)
from x10.perpetual.orderbooks import OrderbookUpdateModel, OrderbookQuantityModel
from x10.perpetual.orders import (
    OpenOrderModel,
    PlacedOrderModel,
    OrderSide,
    OrderType,
    TimeInForce,
    OrderStatus,
)
from x10.perpetual.positions import PositionModel, PositionSide, PositionStatus
from x10.perpetual.trades import AccountTradeModel, TradeType


def create_mock_balance() -> BalanceModel:
    """Create a mock balance for testing."""
    return BalanceModel(
        collateral_name="USD",
        balance=Decimal("10000.00"),
        equity=Decimal("10500.00"),
        available_for_trade=Decimal("8000.00"),
        available_for_withdrawal=Decimal("7500.00"),
        unrealised_pnl=Decimal("500.00"),
        initial_margin=Decimal("2000.00"),
        margin_ratio=Decimal("0.20"),
        updated_time=1700000000000,
    )


def create_mock_position(
    market: str = "BTC-USD",
    side: str = "LONG",
    size: Decimal = Decimal("0.5"),
    open_price: Decimal = Decimal("50000.00"),
    value: Decimal = Decimal("25000.00"),
    unrealised_pnl: Decimal = Decimal("500.00"),
    leverage: int = 10,
) -> PositionModel:
    """Create a mock position for testing."""
    return PositionModel(
        id=1001,
        account_id=1001,
        market=market,
        status=PositionStatus.OPENED,
        side=PositionSide(side),
        size=size,
        open_price=open_price,
        mark_price=Decimal("50500.00"),
        value=value,
        unrealised_pnl=unrealised_pnl,
        realised_pnl=Decimal("0"),
        leverage=Decimal(leverage),
        liquidation_price=Decimal("45000.00"),
        created_at=1700000000000,
        updated_at=1700000000000,
    )


def create_mock_positions() -> List[PositionModel]:
    """Create a list of mock positions for testing."""
    return [
        create_mock_position(
            market="BTC-USD",
            side="LONG",
            size=Decimal("0.5"),
            open_price=Decimal("50000.00"),
            value=Decimal("25000.00"),
            unrealised_pnl=Decimal("500.00"),
            leverage=10,
        ),
        create_mock_position(
            market="ETH-USD",
            side="SHORT",
            size=Decimal("5.0"),
            open_price=Decimal("3000.00"),
            value=Decimal("15000.00"),
            unrealised_pnl=Decimal("-200.00"),
            leverage=5,
        ),
    ]


def create_mock_market_stats() -> MarketStatsModel:
    """Create mock market stats for testing."""
    return MarketStatsModel(
        daily_volume=Decimal("1000000.00"),
        daily_volume_base=Decimal("20.00"),
        daily_price_change=Decimal("500.00"),
        daily_price_change_percentage=Decimal("0.01"),
        daily_low=Decimal("49000.00"),
        daily_high=Decimal("51000.00"),
        last_price=Decimal("50500.00"),
        ask_price=Decimal("50510.00"),
        bid_price=Decimal("50490.00"),
        mark_price=Decimal("50500.00"),
        index_price=Decimal("50500.00"),
        funding_rate=Decimal("0.0001"),
        next_funding_rate=1700000000000,
        open_interest=Decimal("5000000.00"),
        open_interest_base=Decimal("100.00"),
    )


def create_mock_trading_config() -> TradingConfigModel:
    """Create mock trading config for testing."""
    return TradingConfigModel(
        min_order_size=Decimal("0.001"),
        min_order_size_change=Decimal("0.00001"),
        min_price_change=Decimal("0.1"),
        max_market_order_value=Decimal("1000000"),
        max_limit_order_value=Decimal("5000000"),
        max_position_value=Decimal("10000000"),
        max_leverage=Decimal("50"),
        max_num_orders=200,
        limit_price_cap=Decimal("0.05"),
        limit_price_floor=Decimal("0.05"),
        risk_factor_config=[
            RiskFactorConfig(upper_bound=Decimal("400000"), risk_factor=Decimal("0.02")),
        ],
    )


def create_mock_l2_config() -> L2ConfigModel:
    """Create mock L2 config for testing."""
    return L2ConfigModel(
        type="STARKX",
        collateral_id="0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
        collateral_resolution=1000000,
        synthetic_id="0x4254432d3600000000000000000000",
        synthetic_resolution=1000000,
    )


def create_mock_market(name: str = "BTC-USD", active: bool = True) -> MarketModel:
    """Create a mock market for testing."""
    return MarketModel(
        name=name,
        category="L1",
        asset_name=name.split("-")[0],
        asset_precision=5,
        collateral_asset_name="USD",
        collateral_asset_precision=6,
        active=active,
        market_stats=create_mock_market_stats(),
        trading_config=create_mock_trading_config(),
        l2_config=create_mock_l2_config(),
    )


def create_mock_markets() -> List[MarketModel]:
    """Create a list of mock markets for testing."""
    return [
        create_mock_market("BTC-USD"),
        create_mock_market("ETH-USD"),
        create_mock_market("SOL-USD"),
    ]


def create_mock_orderbook() -> OrderbookUpdateModel:
    """Create a mock orderbook for testing."""
    return OrderbookUpdateModel(
        market="BTC-USD",
        bid=[
            OrderbookQuantityModel(price=Decimal("50490.00"), qty=Decimal("1.5")),
            OrderbookQuantityModel(price=Decimal("50480.00"), qty=Decimal("2.0")),
            OrderbookQuantityModel(price=Decimal("50470.00"), qty=Decimal("3.5")),
        ],
        ask=[
            OrderbookQuantityModel(price=Decimal("50510.00"), qty=Decimal("1.2")),
            OrderbookQuantityModel(price=Decimal("50520.00"), qty=Decimal("2.5")),
            OrderbookQuantityModel(price=Decimal("50530.00"), qty=Decimal("4.0")),
        ],
    )


def create_mock_candles() -> List[CandleModel]:
    """Create mock candles for testing."""
    base_ts = 1700000000000
    return [
        CandleModel(
            timestamp=base_ts,
            open=Decimal("50000.00"),
            high=Decimal("50100.00"),
            low=Decimal("49900.00"),
            close=Decimal("50050.00"),
            volume=Decimal("100.5"),
        ),
        CandleModel(
            timestamp=base_ts + 60000,
            open=Decimal("50050.00"),
            high=Decimal("50150.00"),
            low=Decimal("50000.00"),
            close=Decimal("50100.00"),
            volume=Decimal("150.2"),
        ),
        CandleModel(
            timestamp=base_ts + 120000,
            open=Decimal("50100.00"),
            high=Decimal("50200.00"),
            low=Decimal("50050.00"),
            close=Decimal("50180.00"),
            volume=Decimal("120.8"),
        ),
    ]


def create_mock_open_order(
    order_id: int = 12345,
    market: str = "BTC-USD",
    side: str = "BUY",
    price: Decimal = Decimal("50000.00"),
    qty: Decimal = Decimal("0.1"),
    filled_qty: Optional[Decimal] = None,
    external_id: str = "test-order-001",
) -> OpenOrderModel:
    """Create a mock open order for testing."""
    return OpenOrderModel(
        id=order_id,
        account_id=1001,
        external_id=external_id,
        market=market,
        type=OrderType.LIMIT,
        side=OrderSide(side),
        status=OrderStatus.NEW,
        price=price,
        qty=qty,
        filled_qty=filled_qty,
        reduce_only=False,
        post_only=False,
        time_in_force=TimeInForce.GTT,
        created_time=1700000000000,
        updated_time=1700000000000,
    )


def create_mock_open_orders() -> List[OpenOrderModel]:
    """Create a list of mock open orders for testing."""
    return [
        create_mock_open_order(
            order_id=12345,
            market="BTC-USD",
            side="BUY",
            price=Decimal("50000.00"),
            qty=Decimal("0.1"),
            external_id="test-order-001",
        ),
        create_mock_open_order(
            order_id=12346,
            market="ETH-USD",
            side="SELL",
            price=Decimal("3000.00"),
            qty=Decimal("1.0"),
            filled_qty=Decimal("0.5"),
            external_id="test-order-002",
        ),
    ]


def create_mock_placed_order(
    order_id: int = 12345,
    external_id: str = "test-order-001",
) -> PlacedOrderModel:
    """Create a mock placed order response for testing."""
    return PlacedOrderModel(
        id=order_id,
        external_id=external_id,
    )


def create_mock_trade(
    trade_id: int = 98765,
    order_id: int = 12345,
    market: str = "BTC-USD",
    side: str = "BUY",
    price: Decimal = Decimal("50000.00"),
    qty: Decimal = Decimal("0.1"),
    fee: Decimal = Decimal("2.50"),
    is_taker: bool = True,
) -> AccountTradeModel:
    """Create a mock trade for testing."""
    return AccountTradeModel(
        id=trade_id,
        account_id=1001,
        market=market,
        order_id=order_id,
        side=OrderSide(side),
        price=price,
        qty=qty,
        value=price * qty,
        fee=fee,
        is_taker=is_taker,
        trade_type=TradeType.TRADE,
        created_time=1700000000000,
    )


def create_mock_trades() -> List[AccountTradeModel]:
    """Create a list of mock trades for testing."""
    return [
        create_mock_trade(
            trade_id=98765,
            order_id=12345,
            market="BTC-USD",
            side="BUY",
            price=Decimal("50000.00"),
            qty=Decimal("0.1"),
            fee=Decimal("2.50"),
            is_taker=True,
        ),
        create_mock_trade(
            trade_id=98766,
            order_id=12346,
            market="ETH-USD",
            side="SELL",
            price=Decimal("3000.00"),
            qty=Decimal("0.5"),
            fee=Decimal("0.75"),
            is_taker=False,
        ),
    ]


# Pytest fixtures
@pytest.fixture
def mock_balance():
    """Fixture for mock balance."""
    return create_mock_balance()


@pytest.fixture
def mock_position():
    """Fixture for a single mock position."""
    return create_mock_position()


@pytest.fixture
def mock_positions():
    """Fixture for mock positions list."""
    return create_mock_positions()


@pytest.fixture
def mock_market():
    """Fixture for a single mock market."""
    return create_mock_market()


@pytest.fixture
def mock_markets():
    """Fixture for mock markets list."""
    return create_mock_markets()


@pytest.fixture
def mock_orderbook():
    """Fixture for mock orderbook."""
    return create_mock_orderbook()


@pytest.fixture
def mock_candles():
    """Fixture for mock candles."""
    return create_mock_candles()


@pytest.fixture
def mock_open_order():
    """Fixture for a single mock open order."""
    return create_mock_open_order()


@pytest.fixture
def mock_open_orders():
    """Fixture for mock open orders list."""
    return create_mock_open_orders()


@pytest.fixture
def mock_placed_order():
    """Fixture for mock placed order response."""
    return create_mock_placed_order()


@pytest.fixture
def mock_trade():
    """Fixture for a single mock trade."""
    return create_mock_trade()


@pytest.fixture
def mock_trades():
    """Fixture for mock trades list."""
    return create_mock_trades()
