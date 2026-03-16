"""
Account and position transformers.

Converts Extended balance and position data to Hyperliquid format.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from x10.perpetual.balances import BalanceModel
from x10.perpetual.positions import PositionModel

from extended.utils.helpers import to_hyperliquid_market_name


class AccountTransformer:
    """Transform Extended account data to Hyperliquid format."""

    @staticmethod
    def transform_user_state(
        balance: BalanceModel,
        positions: List[PositionModel],
    ) -> Dict[str, Any]:
        """
        Transform Extended balance + positions to Hyperliquid user_state format.

        Args:
            balance: Extended BalanceModel
            positions: List of Extended PositionModel

        Returns:
            Dict in Hyperliquid user_state format
        """
        # Calculate totals
        total_position_value = sum(pos.value for pos in positions)

        # Transform positions
        asset_positions = []
        for pos in positions:
            asset_positions.append(
                AccountTransformer.transform_position(pos)
            )

        return {
            "assetPositions": asset_positions,
            "crossMaintenanceMarginUsed": str(balance.initial_margin),
            "crossMarginSummary": {
                "accountValue": str(balance.equity),
                "totalMarginUsed": str(balance.initial_margin),
                "totalNtlPos": str(total_position_value),
                "totalRawUsd": str(balance.balance),
            },
            "marginSummary": {
                "accountValue": str(balance.equity),
                "totalMarginUsed": str(balance.initial_margin),
                "totalNtlPos": str(total_position_value),
                "totalRawUsd": str(balance.balance),
                "withdrawable": str(balance.available_for_trade),
            },
            "withdrawable": str(balance.available_for_trade),
        }

    @staticmethod
    def transform_position(position: PositionModel) -> Dict[str, Any]:
        """
        Transform Extended position to Hyperliquid assetPosition format.

        Args:
            position: Extended PositionModel

        Returns:
            Dict in Hyperliquid assetPosition format
        """
        # Signed size: positive for LONG, negative for SHORT
        size = position.size
        # Handle both enum and string types for side
        side_value = position.side.value if hasattr(position.side, 'value') else position.side
        szi = str(size) if side_value == "LONG" else str(-size)

        leverage = int(position.leverage)
        margin_used = position.value / leverage if leverage > 0 else Decimal(0)
        roe = (
            position.unrealised_pnl / margin_used
            if margin_used > 0
            else Decimal(0)
        )

        return {
            "position": {
                "coin": to_hyperliquid_market_name(position.market),
                "szi": szi,
                "leverage": {"type": "cross", "value": leverage},
                "entryPx": str(position.open_price),
                "positionValue": str(position.value),
                "unrealizedPnl": str(position.unrealised_pnl),
                "liquidationPx": (
                    str(position.liquidation_price)
                    if position.liquidation_price
                    else None
                ),
                "marginUsed": str(margin_used),
                "returnOnEquity": str(roe),
            },
            "type": "oneWay",
        }

    @staticmethod
    def transform_balance(balance: BalanceModel) -> Dict[str, Any]:
        """
        Transform Extended balance to a simple balance dict.

        Args:
            balance: Extended BalanceModel

        Returns:
            Dict with balance information
        """
        return {
            "balance": str(balance.balance),
            "equity": str(balance.equity),
            "available_for_trade": str(balance.available_for_trade),
            "available_for_withdrawal": str(balance.available_for_withdrawal),
            "unrealised_pnl": str(balance.unrealised_pnl),
            "initial_margin": str(balance.initial_margin),
            "margin_ratio": str(balance.margin_ratio),
        }
