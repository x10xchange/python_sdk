# Extended Python SDK

Python client for [Extended API](https://api.docs.extended.exchange/).

Minimum Python version required to use this library is `3.10`
(you can use [pyenv](https://github.com/pyenv/pyenv) to manage your Python versions easily).

## Installation

```shell
pip install x10-python-trading-starknet
```

Our SDK makes use of a [Rust Library Python Wrapper](https://github.com/x10xchange/stark-crypto-wrapper-py) to speed up signing and hashing of stark components.
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

| Module  | Description                                       |
|---------|---------------------------------------------------|
| auth    | Functionality related to client/account creation. |
| account | Account API keys creation.                        |

### Blocking Trading

Placing orders and receiving updates in a blocking (synchronous) manner.

### REST API

| Module           | Description                                                                                         |
|------------------|-----------------------------------------------------------------------------------------------------|
| account          | Functionality related to managing an active trading account (e.g., leverage/positions/orders/etc).  |
| builder          | Functionality related to builders-specific data.                                                    |
| info             | Functionality related to public market data (including historical data).                            |
| order_management | Functionality related to managing orders (place/cancel).                                            |
| testnet          | Functionality related to TESTNET specific actions (e.g., claiming TESTNET tokens).                  |
| vault            | Functionality related to Vault public data and user's Vault token management (deposits/withrawals). | 

### Streaming

Provides functionality for subscribing to real-time WebSocket updates.
Each topic (stream) requires a separate WebSocket connection.

## Onboarding via SDK

The process of obtaining a Stark key pair from an Ethereum account is a cryptographic procedure
that involves generating a private and public key pair used in the StarkWare ecosystem.
This process leverages the Ethereum account to create a deterministic Stark key pair that can be used
for operations on StarkWare-based systems such as StarkEx and StarkNet.

### Process of Obtaining a Stark Key Pair from an Ethereum Account

1. **Context and Purpose.** StarkWare-based systems require their own cryptographic keys (Stark keys)
   separate from Ethereum keys. However, to maintain a consistent user experience, StarkWare allows users
   to derive these keys deterministically from their existing Ethereum accounts. The process of obtaining
   a Stark key pair from an Ethereum account involves generating a signing message that the Ethereum account
   can sign and then using that signature to derive the Stark private key.
2. **Generating the Signing Structure.** The first step in the process is to generate a signing structure
   that will be signed by the Ethereum account. This structure is constructed using the EIP-712 standard,
   which allows for typed data to be signed in a structured way on Ethereum.
    1. **Define the Signing Structure.** The message to be signed includes: (1) account index,
       (2) the Ethereum wallet address, (3) and whether the terms of service (TOS) are accepted.
       Check `get_key_derivation_struct_to_sign` function implementation for more details.
    2. **EIP-712 Typed Data.** The signing structure uses EIP-712 typed data, which consists of:
        - **Domain.** This is a structured domain object that helps to prevent cross-domain replay attacks.
          In this case, it typically includes the name field (which might be the name of the application or system).
        - **Message.** This is the main data being signed, which includes the accountIndex, wallet address, and tosAccepted fields.
        - **Types.** This describes the types of the fields in both the domain and message.
        - **Primary Type.** This indicates the primary type being signed (in this case, `AccountCreation`).
    3. **Encoding the Typed Data.** The structure is encoded into a format that can be signed by
       the Ethereum account. This is done using the `encode_typed_data` function,
       which creates a `SignableMessage`. The `SignableMessage` includes the hash of the typed data
       according to the EIP-712 standard.
3. **Signing the Structure with the Ethereum Account.** Once the signing structure is prepared,
   it is signed using the Ethereum private key.
4. Deriving the Stark Private Key. The signature obtained from the Ethereum account is then used to
   derive the Stark private key. This is done by truncating the r value from the Ethereum signature and
   using it as the basis for the Stark private key. Check `get_private_key_from_eth_signature` function
   implementation in [Rust Library](https://github.com/x10xchange/rust-crypto-lib-base) for more details.

## Breaking changes

For a detailed list of breaking changes, please refer to the [MIGRATION.md](MIGRATION.md) file.

## Contributing

See the [CONTRIBUTING.md](CONTRIBUTING.md) file.
