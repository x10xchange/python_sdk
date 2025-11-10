import logging
import logging.config
import logging.handlers
import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class EnvConfig:
    api_key: str | None = None
    public_key: str | None = None
    private_key: str | None = None
    vault_id: int | None = None
    builder_id: int | None = None


def init_env(require_private_api: bool = True):
    load_dotenv()

    config_as_str = Path(__file__).parent.joinpath("./logger.yml").read_text()
    config = yaml.safe_load(config_as_str)
    logging.config.dictConfig(config)

    api_key = os.getenv("X10_API_KEY")
    public_key = os.getenv("X10_PUBLIC_KEY")
    private_key = os.getenv("X10_PRIVATE_KEY")
    vault_id = os.getenv("X10_VAULT_ID")
    builder_id = os.getenv("X10_BUILDER_ID")

    if require_private_api:
        assert api_key, "X10_API_KEY is not set"
        assert public_key, "X10_PUBLIC_KEY is not set"
        assert private_key, "X10_PRIVATE_KEY is not set"
        assert vault_id, "X10_VAULT_ID is not set"

        assert public_key.startswith("0x"), "X10_PUBLIC_KEY must be a hex string"
        assert private_key.startswith("0x"), "X10_PRIVATE_KEY must be a hex string"

    return EnvConfig(
        api_key=api_key,
        public_key=public_key,
        private_key=private_key,
        vault_id=int(vault_id) if vault_id else None,
        builder_id=int(builder_id) if builder_id else None,
    )
