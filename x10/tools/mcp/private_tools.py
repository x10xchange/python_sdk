from decimal import Decimal
from typing import Optional

from mcp.server import FastMCP

from x10.clients.rest import RestApiClient
from x10.config import get_config_by_name
from x10.core.env_config import EnvConfig
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.order import OrderSide, OrderType, SelfTradeProtectionLevel, TimeInForce
from x10.signing.order_object import create_order_object
from x10.tools.mcp.utils import serialize_tool_result


def _create_private_rest_api_client() -> RestApiClient:
    env_config = EnvConfig.parse()
    env_config.validate_private_api_credentials()
    client_config = get_config_by_name(env_config.client_config_name)

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return RestApiClient(client_config, stark_account)


def register_tools(mcp: FastMCP):
    @mcp.tool()
    async def place_order(
        market_name: str,
        side: OrderSide,
        amount_of_synthetic: Decimal,
        price: Decimal,
        order_type: OrderType = OrderType.LIMIT,
        post_only: bool = False,
        time_in_force: TimeInForce = TimeInForce.GTT,
        self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
        external_id: Optional[str] = None,
        reduce_only: bool = False,
    ) -> dict:
        """
        Place a new order. Requires authentication env vars.

        Args:
            market_name: Market identifier, e.g. "BTC-USD".
            side: Order side, one of "BUY" or "SELL".
            amount_of_synthetic: Order quantity in base asset units.
            price: Limit price.
            order_type: One of "LIMIT", "MARKET". Defaults to "LIMIT".
            post_only: If True, the order will be rejected if it would trade immediately.
            time_in_force: One of "GTT", "IOC", "FOK". Defaults to "GTT".
            self_trade_protection_level: One of "DISABLED", "ACCOUNT", "CLIENT". Defaults to "ACCOUNT".
            external_id: Optional client-assigned order ID.
            reduce_only: If True, the order will only reduce an existing position.
        """
        async with _create_private_rest_api_client() as client:
            markets = await client.info.get_markets_dict()
            market = markets[market_name]

            order = create_order_object(
                account=client.stark_account,
                starknet_domain=client.config.signing.starknet_domain,
                market=market,
                side=side,
                amount_of_synthetic=amount_of_synthetic,
                price=price,
                order_type=order_type,
                post_only=post_only,
                time_in_force=time_in_force,
                self_trade_protection_level=self_trade_protection_level,
                order_external_id=external_id,
                reduce_only=reduce_only,
            )

            result = await client.orders.place_order(order=order)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_balance() -> dict:
        """
        Get account balance. Requires authentication env vars.
        """
        async with _create_private_rest_api_client() as client:
            result = await client.account.get_balance()
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_positions(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get open positions. Requires authentication env vars.

        Args:
            market_names: Optional list of market names to filter.
        """
        async with _create_private_rest_api_client() as client:
            result = await client.account.get_positions(market_names=market_names)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_open_orders(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get open orders. Requires authentication env vars.

        Args:
            market_names: Optional list of market names to filter.
        """
        async with _create_private_rest_api_client() as client:
            result = await client.account.get_open_orders(market_names=market_names)
            return serialize_tool_result(result.data)
