import os
from dataclasses import dataclass
from typing import Literal

from utils.string import is_hex_string

from x10.errors import ValidationError


@dataclass
class EnvConfig:
    client_config_name: Literal["TESTNET", "MAINNET"]
    api_key: str | None = None
    public_key: str | None = None
    private_key: str | None = None
    vault_id: int | None = None
    builder_id: int | None = None

    @staticmethod
    def parse():
        api_key = os.getenv("X10_API_KEY")
        public_key = os.getenv("X10_PUBLIC_KEY")
        private_key = os.getenv("X10_PRIVATE_KEY")
        vault_id = os.getenv("X10_VAULT_ID")
        builder_id = os.getenv("X10_BUILDER_ID")
        client_config_name = os.getenv("X10_CLIENT_CONFIG_NAME", "TESTNET").upper()

        if client_config_name != "TESTNET" or client_config_name != "MAINNET":
            raise ValidationError("X10_CLIENT_CONFIG_NAME must be either TESTNET or MAINNET")

        if public_key:
            assert is_hex_string(public_key), "X10_PUBLIC_KEY must be a hex string"

        if private_key:
            assert is_hex_string(private_key), "X10_PRIVATE_KEY must be a hex string"

        return EnvConfig(
            client_config_name=client_config_name,
            api_key=api_key,
            public_key=public_key.lower() if public_key else None,
            private_key=private_key.lower() if private_key else None,
            vault_id=int(vault_id) if vault_id else None,
            builder_id=int(builder_id) if builder_id else None,
        )
