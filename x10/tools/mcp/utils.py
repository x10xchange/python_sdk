from typing import Any

from x10.clients.rest import RestApiClient
from x10.config import get_config_by_name
from x10.core.env_config import EnvConfig
from x10.core.stark_account import StarkPerpetualAccount


def create_private_rest_api_client() -> RestApiClient:
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


def serialize_tool_result(obj: Any) -> Any:
    if obj is None:
        return None

    if hasattr(obj, "to_api_request_json"):
        return obj.to_api_request_json()

    if isinstance(obj, list):
        return [serialize_tool_result(item) for item in obj]

    return obj
