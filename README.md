# Extended Python SDK

Python client for [Extended API](https://api.docs.extended.exchange/).

Minimum Python version required to use this library is `3.10`
(you can use [pyenv](https://github.com/pyenv/pyenv) to manage your Python versions easily).

## Installation

```shell
pip install x10-python-trading-starknet
```

Our SDK makes use of a [Rust Library](https://github.com/x10xchange/stark-crypto-wrapper-py) to speed up signing and hashing of stark components.
Currently, this library supports the following environments (please refer to the library repository for the most up to date information):

|                       | 3.9 | 3.10 | 3.11 | 3.12 | 3.13 |
|-----------------------|:---:|:----:|:----:|:----:|:----:|
| linux (glibc) - x86   |  ✅  |  ✅   |  ✅   |  ✅   |  ✅   |
| linux (musl) - x86    |  ✅  |  ✅   |  ✅   |  ✅   |  ✅   |
| linux (glibc) - arm64 |  ✅  |  ✅   |  ✅   |  ✅   |  ✅   |
| linux (musl) - arm64  |  ✅  |  ✅   |  ✅   |  ✅   |  ✅   |
| OSX - arm64           |  ✅  |  ✅   |  ✅   |  ✅   |  ✅   |
| windows - x86         |  ✅  |  ✅   |  ✅   |  ✅   |  ✅   |
| windows - arm64       | ⚠️  |  ⚠️  |  ⚠️  |  ⚠️  |  ⚠️  |

## TLDR

Register at [Extended Testnet](https://starknet.sepolia.extended.exchange/). 

Navigate to [API Management](https://starknet.sepolia.extended.exchange/api-management):
1. Generate an API key
2. Show API details (you will need these details to initialize a trading client)

Create an `.env` file (see below) in the examples directory root:
```properties
X10_API_KEY=<your_api_key>
X10_PUBLIC_KEY=<your_public_key>
X10_PRIVATE_KEY=<your_private_key>
X10_VAULT_ID=<your_vault_id>
```

Refer to the [cases](./examples/cases) directory for the specific examples of how to use the SDK.

Each example follows the same pattern:
```python
from dotenv import load_dotenv
from x10.core.env_config import EnvConfig
from x10.core.stark_account import StarkPerpetualAccount
from x10.config import TESTNET_CONFIG
from x10.clients.rest import RestApiClient


# Load environment variables from `.env` file and parse them into a `EnvConfig` object.
load_dotenv()
env_config = EnvConfig.parse()
env_config.validate_private_api_credentials()

# Instantiate a `StarkPerpetualAccount` object with the parsed environment variables.
stark_account = StarkPerpetualAccount(
    api_key=env_config.api_key,
    public_key=env_config.public_key,
    private_key=env_config.private_key,
    vault=env_config.vault_id,
)

# Instantiate REST API/Streaming/etc client. `stark_account` can be omitted
# if you don't need to make private API requests.
rest_client = RestApiClient(TESTNET_CONFIG, stark_account)

# Perform example action using the instantiated client.
```

## OpenAPI Specifications

Available specifications can be found in the [specs](./specs) directory.

## Clients

The SDK currently provides functionality using so-called clients.
And each client is divided into feature-specific modules.

### Onboarding

| Module  | Description |
|---------|-------------|
| auth    | TBD         |
| account | TBD         |

### Blocking Trading

### REST API

| Module           | Description                                                          |
|------------------|----------------------------------------------------------------------|
| account          | Exposes functionality related to managing an active trading account. |
| builder          | TBD                                                                  |
| info             | TBD                                                                  |
| order_management | TBD                                                                  |
| testnet          | TBD                                                                  |
| vault            | TBD                                                                  |

### Streaming

## Tools
