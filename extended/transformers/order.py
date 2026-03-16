"""
Order and trade transformers.

Converts Extended order and trade data to Hyperliquid format.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from x10.perpetual.orders import OpenOrderModel, PlacedOrderModel
from x10.perpetual.trades import AccountTradeModel

from extended.utils.constants import SIDE_TO_HL
from extended.utils.helpers import to_hyperliquid_market_name


class OrderTransformer:
    """Transform Extended order data to Hyperliquid format."""

    @staticmethod
    def transform_open_orders(orders: List[OpenOrderModel]) -> List[Dict[str, Any]]:
        """
        Transform Extended orders to Hyperliquid open_orders format.

        Args:
            orders: List of Extended OpenOrderModel

        Returns:
            List of orders in Hyperliquid format
        """
        return [
            OrderTransformer.transform_open_order(order)
            for order in orders
        ]

    @staticmethod
    def transform_open_order(order: OpenOrderModel) -> Dict[str, Any]:
        """
        Transform a single Extended order to Hyperliquid format.

        Args:
            order: Extended OpenOrderModel

        Returns:
            Dict in Hyperliquid open order format
        """
        # Calculate remaining size
        filled_qty = order.filled_qty if order.filled_qty else Decimal(0)
        remaining_sz = order.qty - filled_qty

        # Handle both enum and string types for side
        side_value = order.side.value if hasattr(order.side, 'value') else order.side
        return {
            "coin": to_hyperliquid_market_name(order.market),
            "side": SIDE_TO_HL.get(side_value, "B"),
            "limitPx": str(order.price),
            "sz": str(remaining_sz),
            "oid": order.id,
            "timestamp": order.created_time,
            "origSz": str(order.qty),
            "cloid": order.external_id if order.external_id else None,
        }

    @staticmethod
    def transform_user_fills(trades: List[AccountTradeModel]) -> List[Dict[str, Any]]:
        """
        Transform Extended trades to Hyperliquid user_fills format.

        Args:
            trades: List of Extended AccountTradeModel

        Returns:
            List of fills in Hyperliquid format
        """
        return [
            OrderTransformer.transform_fill(trade)
            for trade in trades
        ]

    @staticmethod
    def transform_fill(trade: AccountTradeModel) -> Dict[str, Any]:
        """
        Transform a single Extended trade to Hyperliquid fill format.

        Note: The `cloid` field will be None because Extended's trades endpoint
        does not include the client order ID (external_id).

        Args:
            trade: Extended AccountTradeModel

        Returns:
            Dict in Hyperliquid fill format
        """
        # Handle both enum and string types for side and trade_type
        side_value = trade.side.value if hasattr(trade.side, 'value') else trade.side
        trade_type_value = trade.trade_type.value if hasattr(trade.trade_type, 'value') else trade.trade_type
        return {
            "coin": to_hyperliquid_market_name(trade.market),
            "px": str(trade.price),
            "sz": str(trade.qty),
            "side": SIDE_TO_HL.get(side_value, "B"),
            "time": trade.created_time,
            "startPosition": "0",  # Not available from Extended
            "dir": "Trade",  # Can't determine Open/Close from Extended trades
            "closedPnl": "0",  # Not in trade response
            "hash": str(trade.id),
            "oid": trade.order_id,
            "crossed": trade.is_taker,
            "fee": str(trade.fee),
            "tid": trade.id,
            "liquidation": trade_type_value == "LIQUIDATION",
            "cloid": None,  # Not available from Extended trades endpoint
        }

    @staticmethod
    def transform_order_response(
        placed_order: PlacedOrderModel,
    ) -> Dict[str, Any]:
        """
        Transform Extended order placement response to Hyperliquid format.

        Args:
            placed_order: Extended PlacedOrderModel

        Returns:
            Dict in Hyperliquid order response format
        """
        return {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {
                            "resting": {
                                "oid": placed_order.id,
                                "cloid": placed_order.external_id,
                            }
                        }
                    ]
                },
            },
        }

    @staticmethod
    def transform_cancel_response(
        success: bool = True,
        order_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Transform Extended cancel response to Hyperliquid format.

        Args:
            success: Whether the cancel was successful
            order_id: The order ID that was cancelled

        Returns:
            Dict in Hyperliquid cancel response format
        """
        if success:
            return {
                "status": "ok",
                "response": {
                    "type": "cancel",
                    "data": {
                        "statuses": ["success"]
                    },
                },
            }
        else:
            return {
                "status": "err",
                "response": "Cancel failed",
            }

    @staticmethod
    def transform_error_response(
        message: str,
    ) -> Dict[str, Any]:
        """
        Transform an error to Hyperliquid error format.

        Args:
            message: Error message

        Returns:
            Dict in Hyperliquid error response format
        """
        return {
            "status": "err",
            "response": message,
        }

    @staticmethod
    def transform_bulk_orders_response(
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Transform bulk order results to Hyperliquid format.

        Args:
            results: List of individual order results

        Returns:
            Dict in Hyperliquid bulk order response format
        """
        statuses = []
        for result in results:
            if result.get("status") == "ok":
                data = result.get("data", {})
                statuses.append({
                    "resting": {
                        "oid": data.get("id"),
                        "cloid": data.get("external_id"),
                    }
                })
            else:
                statuses.append({
                    "error": result.get("error", "Unknown error")
                })

        return {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": statuses
                },
            },
        }

    @staticmethod
    def transform_leverage_response() -> Dict[str, Any]:
        """
        Transform leverage update response to Hyperliquid format.

        Returns:
            Dict in Hyperliquid leverage response format
        """
        return {
            "status": "ok",
            "response": {
                "type": "leverage",
            },
        }
