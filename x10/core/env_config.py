import os
from dataclasses import dataclass

from x10.core.client_config import ClientConfigName
from x10.errors import ValidationError
from x10.utils.string import is_hex_string


@dataclass
class EnvConfig:
    client_config_name: ClientConfigName
    api_key: str | None = None
    public_key: str | None = None
    private_key: str | None = None
    vault_id: int | None = None
    builder_id: int | None = None

    @staticmethod
    def parse():
        client_config_name = os.getenv("X10_CLIENT_CONFIG_NAME", default="TESTNET").upper()
        api_key = os.getenv("X10_API_KEY")
        public_key = os.getenv("X10_PUBLIC_KEY")
        private_key = os.getenv("X10_PRIVATE_KEY")
        vault_id = os.getenv("X10_VAULT_ID")
        builder_id = os.getenv("X10_BUILDER_ID")

        if client_config_name != "TESTNET" and client_config_name != "MAINNET":
            raise ValidationError("X10_CLIENT_CONFIG_NAME must be either TESTNET or MAINNET")

        if public_key:
            assert is_hex_string(public_key), "X10_PUBLIC_KEY must be a hex string"

        if private_key:
            assert is_hex_string(private_key), "X10_PRIVATE_KEY must be a hex string"

        return EnvConfig(
            client_config_name=client_config_name,  # type: ignore[arg-type]
            api_key=api_key,
            public_key=public_key.lower() if public_key else None,
            private_key=private_key.lower() if private_key else None,
            vault_id=int(vault_id) if vault_id else None,
            builder_id=int(builder_id) if builder_id else None,
        )

    def validate_private_api_credentials(self):
        if not self.api_key:
            raise ValidationError("X10_API_KEY is not set")

        if not self.public_key:
            raise ValidationError("X10_PUBLIC_KEY is not set")

        if not self.private_key:
            raise ValidationError("X10_PRIVATE_KEY is not set")

        if not self.vault_id:
            raise ValidationError("X10_VAULT_ID is not set")
