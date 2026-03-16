"""
Type definitions for Extended Exchange SDK.

Provides type aliases and dataclasses for the Hyperliquid-compatible interface.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union


# Re-export x10 types for internal use
from x10.perpetual.orders import (
    OrderSide,
    OrderType as X10OrderType,
    TimeInForce as X10TimeInForce,
    OrderStatus,
    SelfTradeProtectionLevel,
)
from x10.perpetual.positions import PositionSide, PositionStatus
from x10.perpetual.candles import CandleType, CandleInterval


class Side(str, Enum):
    """Order side in Hyperliquid format."""

    BUY = "B"
    SELL = "A"

    @classmethod
    def from_is_buy(cls, is_buy: bool) -> "Side":
        """Convert is_buy boolean to Side."""
        return cls.BUY if is_buy else cls.SELL

    @classmethod
    def from_x10_side(cls, side: Union[OrderSide, PositionSide, str]) -> "Side":
        """Convert x10 side to Hyperliquid side."""
        side_str = str(side).upper()
        if side_str in ("BUY", "LONG"):
            return cls.BUY
        return cls.SELL

    def to_is_buy(self) -> bool:
        """Convert to is_buy boolean."""
        return self == Side.BUY


class TimeInForce(str, Enum):
    """Time in force options in Hyperliquid format."""

    GTC = "Gtc"  # Good-till-cancel (maps to GTT in Extended)
    IOC = "Ioc"  # Immediate-or-cancel
    ALO = "Alo"  # Add-liquidity-only (post-only)

    def to_x10_tif(self) -> X10TimeInForce:
        """Convert to x10 TimeInForce."""
        mapping = {
            TimeInForce.GTC: X10TimeInForce.GTT,
            TimeInForce.IOC: X10TimeInForce.IOC,
            TimeInForce.ALO: X10TimeInForce.GTT,  # ALO uses GTT with post_only=True
        }
        return mapping[self]

    @property
    def is_post_only(self) -> bool:
        """Check if this TIF implies post-only."""
        return self == TimeInForce.ALO


@dataclass
class LimitOrderType:
    """Limit order type specification."""

    tif: TimeInForce = TimeInForce.GTC


@dataclass
class OrderTypeSpec:
    """
    Order type specification in Hyperliquid format.

    Example:
        {"limit": {"tif": "Gtc"}}
        {"limit": {"tif": "Ioc"}}
        {"limit": {"tif": "Alo"}}
    """

    limit: LimitOrderType

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderTypeSpec":
        """Create from dictionary."""
        if "limit" in data:
            limit_data = data["limit"]
            tif = TimeInForce(limit_data.get("tif", "Gtc"))
            return cls(limit=LimitOrderType(tif=tif))
        # Default to GTC limit
        return cls(limit=LimitOrderType())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"limit": {"tif": self.limit.tif.value}}


@dataclass
class BuilderInfo:
    """
    Builder fee information in Hyperliquid format.

    Attributes:
        b: Builder ID as string
        f: Fee in tenths of basis points (10 = 1 bps = 0.0001)

    Example:
        BuilderInfo(b="123", f=10)  # 1 bps fee to builder 123
    """

    b: str  # Builder ID
    f: int  # Fee in tenths of bps

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["BuilderInfo"]:
        """Create from dictionary."""
        if data is None:
            return None
        return cls(b=str(data["b"]), f=int(data["f"]))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"b": self.b, "f": self.f}

    @property
    def builder_id(self) -> int:
        """Get builder ID as integer."""
        return int(self.b)

    @property
    def fee_decimal(self) -> Decimal:
        """
        Convert fee to decimal rate.

        f=1  -> 0.1 bps  -> 0.000001
        f=10 -> 1 bps    -> 0.0001
        f=50 -> 5 bps    -> 0.0005
        """
        return Decimal(self.f) / Decimal(100000)


# Type aliases for Hyperliquid-compatible structures

OrderRequest = TypedDict(
    "OrderRequest",
    {
        "name": str,
        "is_buy": bool,
        "sz": float,
        "limit_px": float,
        "order_type": Dict[str, Any],
        "reduce_only": bool,
        "cloid": Optional[str],
        "builder": Optional[Dict[str, Any]],
    },
    total=False,
)

CancelRequest = TypedDict(
    "CancelRequest",
    {
        "coin": str,
        "oid": Optional[int],
        "cloid": Optional[str],
    },
    total=False,
)


# Hyperliquid-format response types

class LeverageInfo(TypedDict):
    """Leverage information in Hyperliquid format."""

    type: Literal["cross", "isolated"]
    value: int


class PositionInfo(TypedDict, total=False):
    """Position information in Hyperliquid format."""

    coin: str
    szi: str  # Signed size (negative for short)
    leverage: LeverageInfo
    entryPx: str
    positionValue: str
    unrealizedPnl: str
    liquidationPx: Optional[str]
    marginUsed: str
    returnOnEquity: str
    maxTradeSz: str


class AssetPosition(TypedDict):
    """Asset position wrapper in Hyperliquid format."""

    position: PositionInfo
    type: Literal["oneWay"]


class MarginSummary(TypedDict):
    """Margin summary in Hyperliquid format."""

    accountValue: str
    totalMarginUsed: str
    totalNtlPos: str
    totalRawUsd: str


class UserState(TypedDict, total=False):
    """User state response in Hyperliquid format."""

    assetPositions: List[AssetPosition]
    crossMaintenanceMarginUsed: str
    crossMarginSummary: MarginSummary
    marginSummary: Dict[str, str]
    withdrawable: str


class OpenOrder(TypedDict, total=False):
    """Open order in Hyperliquid format."""

    coin: str
    side: Literal["B", "A"]
    limitPx: str
    sz: str
    oid: int
    timestamp: int
    origSz: str
    cloid: Optional[str]


class Fill(TypedDict, total=False):
    """Trade fill in Hyperliquid format."""

    coin: str
    px: str
    sz: str
    side: Literal["B", "A"]
    time: int
    startPosition: str
    dir: str
    closedPnl: str
    hash: str
    oid: int
    crossed: bool
    fee: str
    tid: int
    liquidation: bool
    cloid: Optional[str]


class L2Level(TypedDict):
    """Order book level in Hyperliquid format."""

    px: str
    sz: str
    n: int


class L2Snapshot(TypedDict):
    """Order book snapshot in Hyperliquid format."""

    coin: str
    levels: List[List[L2Level]]  # [bids, asks]
    time: int


class Candle(TypedDict):
    """Candle data in Hyperliquid format."""

    t: int  # Open timestamp
    T: int  # Close timestamp
    s: str  # Symbol
    i: str  # Interval
    o: str  # Open
    c: str  # Close
    h: str  # High
    l: str  # Low
    v: str  # Volume
    n: int  # Number of trades


class UniverseItem(TypedDict):
    """Market info in Hyperliquid universe format."""

    name: str
    szDecimals: int
    maxLeverage: int
    onlyIsolated: bool


class Meta(TypedDict):
    """Exchange metadata in Hyperliquid format."""

    universe: List[UniverseItem]


class OrderStatus(TypedDict, total=False):
    """Order status in response."""

    resting: Dict[str, Any]
    filled: Dict[str, Any]
    error: str


class OrderResponse(TypedDict):
    """Order placement response in Hyperliquid format."""

    status: Literal["ok", "err"]
    response: Dict[str, Any]


class CancelResponse(TypedDict):
    """Cancel response in Hyperliquid format."""

    status: Literal["ok", "err"]
    response: Dict[str, Any]
