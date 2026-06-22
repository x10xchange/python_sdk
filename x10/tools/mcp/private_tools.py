from typing import Optional

from mcp.server import FastMCP

from x10.clients.rest import RestApiClient
from x10.config import get_config_by_name
from x10.core.env_config import EnvConfig
from x10.core.stark_account import StarkPerpetualAccount
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
