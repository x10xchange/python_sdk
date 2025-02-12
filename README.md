# Extended Python SDK

Python client for [Extended API](https://api.docs.extended.exchange/).

Minimum Python version required to use this library is `3.10` (you can use [pyenv](https://github.com/pyenv/pyenv) to manage your Python versions easily).

## Installation 

```shell
pip install x10-python-trading
```

Our SDK makes use of a [Rust Library](https://github.com/x10xchange/stark-crypto-wrapper) to accelerate signing and hashing of stark components. Currently this library supports the following environments

|                       |  3.9  | 3.10  | 3.11  | 3.12  |
| --------------------- | :---: | :---: | :---: | :---: |
| linux (glibc) - x86   |   ✅   |   ✅   |   ✅   |   ✅   |
| linux (musl) - x86    |   ✅   |   ✅   |   ✅   |   ✅   |
| linux (glibc) - arm64 |   ✅   |   ✅   |   ✅   |   ✅   |
| linux (musl) - arm64  |   ✅   |   ✅   |   ✅   |   ✅   |
| OSX - arm64           |   ✅   |   ✅   |   ✅   |   ✅   |
| windows - x86         |   ⚠️   |   ⚠️   |   ⚠️   |   ⚠️   |
| windows - arm64       |   ⚠️   |   ⚠️   |   ⚠️   |   ⚠️   |



## TLDR:

Register at [Extended Testnet](https://testnet.extended.exchange/) by connecting a supported Ethereum Wallet. 

Navigate to [Api Management](https://testnet.extended.exchange/api-management)
1. Generate an API key
2. Show API details (You will need these details to initialise a trading client)

Instantiate a Trading Account

```python 
from x10.perpetual.accounts import StarkPerpetualAccount
api_key:str = "<api>" #from api-management
public_key:str = "<public>" #from api-management
private_key:str = "<private>" #from api-management
vault:int = <vault> #from api-management

stark_account = StarkPerpetualAccount(
    vault=vault,
    private_key=private_key,
    public_key=public_key,
    api_key=api_key,
)
```

Instantiate a Trading Client
```python
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orders import OrderSide
from x10.perpetual.trading_client import PerpetualTradingClient

trading_client = PerpetualTradingClient.create(TESTNET_CONFIG, stark_account)
placed_order = await trading_client.place_order(
    market_name="BTC-USD",
    amount_of_synthetic=Decimal("1"),
    price=Decimal("63000.1"),
    side=OrderSide.SELL,
)
await trading_client.orders.cancel_order(order_id=placed_order.id)
print(placed_order)
```

for more information see [placing an order example](examples/placed_order_example_simple.py).

There is also a skeleton implementation of a [blocking client](examples/simple_client_example.py).

## Modules

The SDK currently provides functionality across three main modules

### Order Management Module 
The order module is accessed using the `orders` property of the trading client
```python
trading_client.orders
```
TODO

### Account Module 
The account module is accessed using the account property of the trading client
```python
trading_client.account
```

it exposes functionality related to managing an active trading account

#### `get_balance`
Fetches the balance of the user's account.

```python
    logger = logging.getLogger("demo_logger")
    balance = await trading_client.account.get_balance()
    logger.info("Balance: %s", balance.to_pretty_json())
```

#### `get_positions`
Fetches the current positions of the user's account. It can filter the positions based on market names and position side.

```python
    logger = logging.getLogger("demo_logger")
    positions = await trading_client.account.get_positions()
    logger.info("Positions: %s", positions.to_pretty_json())
```

returns a list of
```python
class PositionModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    side: PositionSide
    leverage: Decimal
    size: Decimal
    value: Decimal
    open_price: Decimal
    mark_price: Decimal
    liquidation_price: Optional[Decimal] = None
    unrealised_pnl: Decimal
    realised_pnl: Decimal
    tp_price: Optional[Decimal] = None
    sl_price: Optional[Decimal] = None
    adl: Optional[int] = None
    created_at: int
    updated_at: int
```

#### `get_positions_history`
Fetches the historical positions of the user's account. It can filter the positions based on market names and position side.

```python
    logger = logging.getLogger("demo_logger")
    positions = await trading_client.account.get_positions_history()
    logger.info("Positions: %s", positions.to_pretty_json())
```

returns a list of 
```python
class PositionHistoryModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    side: PositionSide
    leverage: Decimal
    size: Decimal
    open_price: Decimal
    exit_type: Optional[ExitType]
    exit_price: Optional[Decimal]
    realised_pnl: Decimal
    created_time: int
    closed_time: Optional[int]
```

#### `get_open_orders`
Fetches the open orders of the user's account. It can filter the orders based on market names, order type, and order side.

```python
    open_orders = await trading_client.account.get_open_orders()
    await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])
```
returns a list of
```python 
class OpenOrderModel(X10BaseModel):
    id: int
    account_id: int
    external_id: str
    market: str
    type: OrderType
    side: OrderSide
    status: OrderStatus
    status_reason: Optional[OrderStatusReason] = None
    price: Decimal
    average_price: Optional[Decimal] = None
    qty: Decimal
    filled_qty: Optional[Decimal] = None
    reduce_only: bool
    post_only: bool
    created_time: int
    updated_time: int
    expiry_time: Optional[int] = None
```

#### `get_orders_history`
Fetches the historical orders of the user's account. It can filter the orders based on market names, order type, and order side

```python
    market_names: Optional[List[str]] = None, #parameter to filter by market
    order_type: Optional[OrderType] = None, #parameter to filter by order type (IOC, GTT etc)
    order_side: Optional[OrderSide] = None, #parameter to filter by side (BUY/SELL)
    cursor: Optional[int] = None, #pagination cursor
    limit: Optional[int] = None, #limit the number of returned orders per page
```

```python
    open_orders = await trading_client.account.get_orders_history(
        market_names=["BTC-USD", "SOL-USD"],
        order_side=OrderSide.BUY
    )
```
returns a list of `OpenOrderModel`

#### `get_trades`
Fetches the trades of the user's account. It can filter the trades based on market names, trade side, and trade type.

```python
```

#### `get_fees`
Fetches the trading fees for the specified markets.

```python
pass
```

#### `get_leverage`
Fetches the leverage for the specified markets.

```python
   leverage = await trading_client.account.get_leverage(market_names=list("BTC-USD"))
   print(leverage)
```

returns a list of
```python
class AccountLeverage(X10BaseModel):
    market: str
    leverage: Decimal
```

#### `update_leverage`
Updates the leverage for a specific market.

```python
    await trading_client.account.update_leverage(market_name="BTC-USD", leverage=Decimal("20.0"))
```

### Markets Info Module 
The markets module is accessed using the `markets_info` property of the trading client
```python
trading_client.markets_info
```
TODO

## SDK Environment configurations (Since version 0.3.0)

The SDK is controlled by an `EndpointConfiguration` object passed to the various methods and clients, several helpful instances are defined in [configuration.py](x10/perpetual/configuration.py)

### `MAINNET_CONFIG` vs `MAINNET_CONFIG_LEGACY_SIGNING_DOMAIN`
If you previously onboarded to our mainnet environment on `app.x10.exchange`, you should use the `MAINNET_CONFIG_LEGACY_SIGNING_DOMAIN` configuration bundle, as this will allow you to regenerate the same l2 keys as were created by our mainnet environment that was running on a legacy domain. 

All new accounts should use the `MAINNET_CONFIG` configuration bundle.

## OnBoarding via SDK (Since Version 0.3.0)

To onboard to the Extended Exchange, the `UserClient` defined in [user_client.py](x10/perpetual/user_client/user_client.py) provides a way to use an Ethereum account to onboard onto the Extended Exchange. 

### TLDR - Check out: [onboarding_example.py](examples/onboarding_example.py)

### `onboard(referral_code: Optional[str] = None) -> OnBoardedAccount`
This method handles the onboarding process of a user. It generates an L2 key pair from the user's L1 Ethereum account, creates an onboarding payload, and sends it to the onboarding endpoint. Upon successful onboarding, it returns an `OnBoardedAccount` object containing the default account and the L2 key pair.

### `onboard_subaccount(account_index: int, description: str | None = None) -> OnBoardedAccount`
This method onboards a subaccount associated with the user's main account. It allows you to specify an `account_index` and an optional description. If a subaccount with the given index already exists, it retrieves and returns that subaccount. Otherwise, it creates a new subaccount and returns an `OnBoardedAccount` object with the subaccount details and the associated L2 key pair.

### `get_accounts() -> List[OnBoardedAccount]`
This method retrieves all the accounts associated with the user. It returns a list of `OnBoardedAccount` objects, each containing the account details and corresponding L2 key pair.

### `create_account_api_key(account: AccountModel, description: str | None) -> str`
This method generates an API key for a specified account. You can provide an optional description for the API key. It returns the newly created API key as a string.

### `perform_l1_withdrawal() -> str`
This method initiates a withdrawal from Layer 2 (L2) to Layer 1 (L1) using the user's Ethereum account. It calls the underlying contract function to perform the withdrawal and returns a string, typically a transaction hash or status.

### `available_l1_withdrawal_balance() -> Decimal`
This method retrieves the available balance for L1 withdrawals. It calls the underlying contract function to fetch the withdrawal balance and returns the balance as a `Decimal` value.

### Process of Obtaining a Stark Key Pair from an Ethereum Account

The process of obtaining a Stark key pair from an Ethereum account is a cryptographic procedure that involves generating a private and public key pair used in the StarkWare ecosystem. This process leverages the Ethereum account to create a deterministic Stark key pair that can be used for operations on StarkWare-based systems such as StarkEx and StarkNet

#### 1. Context and Purpose

StarkWare-based systems require their own cryptographic keys (Stark keys) separate from Ethereum keys. However, to maintain a consistent user experience, StarkWare allows users to derive these keys deterministically from their existing Ethereum accounts. The process of obtaining a Stark key pair from an Ethereum account involves generating a signing message that the Ethereum account can sign, and then using that signature to derive the Stark private key.

#### 2. Generating the Signing Structure

The first step in the process is to generate a signing structure that will be signed by the Ethereum account. This structure is constructed using the EIP-712 standard, which allows for typed data to be signed in a structured way on Ethereum.

##### a. Define the Signing Structure

The message to be signed includes:
1. account index, 
2. the Ethereum wallet address, 
3. and whether the terms of service (TOS) are accepted. 

in the function `get_key_derivation_struct_to_sign`, the signing structure is constructed as follows:

```python
def get_key_derivation_struct_to_sign(account_index: int, address: str, signing_domain: str) -> SignableMessage:
    primary_type = "AccountCreation"
    domain = {"name": signing_domain}
    message = {
        "accountIndex": account_index,
        "wallet": address,
        "tosAccepted": True,
    }
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
        ],
        "AccountCreation": [
            {"name": "accountIndex", "type": "int8"},
            {"name": "wallet", "type": "address"},
            {"name": "tosAccepted", "type": "bool"},
        ],
    }
    structured_data = {
        "types": types,
        "domain": domain,
        "primaryType": primary_type,
        "message": message,
    }
    return encode_typed_data(full_message=structured_data)
```

##### b. EIP-712 Typed Data

The signing structure uses EIP-712 typed data, which consists of:

    Domain: This is a structured domain object that helps to prevent cross-domain replay attacks. In this case, it typically includes the name field (which might be the name of the application or system).

    Message: This is the main data being signed, which includes the accountIndex, wallet address, and tosAccepted fields.

    Types: This describes the types of the fields in both the domain and message.

    Primary Type: This indicates the primary type being signed (in this case, "AccountCreation").

##### c. Encoding the Typed Data

The structure is encoded into a format that can be signed by the Ethereum account. This is done using the `encode_typed_data` function, which creates a `SignableMessage`. The `SignableMessage` includes the hash of the typed data according to the EIP-712 standard.

#### 3. Signing the Structure with the Ethereum Account

Once the signing structure is prepared, it is signed using the Ethereum private key.

#### 4. Deriving the Stark Private Key

The signature obtained from the Ethereum account is then used to derive the Stark private key. This is done by truncating the r value from the Ethereum signature and using it as the basis for the Stark private key:

```python 
def get_private_key_from_eth_signature(eth_signature: str) -> int:
    eth_sig_truncated = re.sub("^0x", "", eth_signature)
    r = eth_sig_truncated[:64]
    return stark_sign.grind_key(int(r, 16), stark_sign.EC_ORDER)
```

`stark_sign.grind_key` is a function imported from [`vendor/starkware/crypto/signature/signature.py`](vendor/starkware/crypto/signature/signature.py) 

## Depositing via SDK (Since Version 0.3.0)

There is a new function `deposit` available on the [`AccountModule`](x10/perpetual/trading_client/account_module.py) which provides the ability to directly deposit USDC into your StarkEx account. For more details check out `call_stark_perpetual_deposit` in [contract.py](x10/perpetual/contract.py)


## Contribution

Make sure you have [poetry](https://python-poetry.org/) installed.

- Clone the repository: `git@github.com:x10xchange/python_sdk.git`
- Navigate to the project directory: `cd python_sdk`
- Create a virtual environment: `poetry shell`
- Install dependencies: `poetry install`
- Update `examples/placed_order_example.py` with your credentials
- Run it: `python -m examples.placed_order_example`

Custom commands:
- `make format` - format code with `black`
- `make lint` - run `safety`, `black`, `flake8` and `mypy` checks
- `make test` - run tests


