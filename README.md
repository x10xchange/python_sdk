# X10

Python client for [X10 API](https://x101.docs.apiary.io).

Minimum Python version required to use this library is `3.9` (you can use [pyenv](https://github.com/pyenv/pyenv) to manage your Python versions easily).

## Installation 

```shell
pip install x10-python-trading
```

Our SDK makes use of a [Rust Library](https://github.com/x10xchange/stark-crypto-wrapper) to accelerate signing and hashing of stark components. Currently this library supports the following environments

|                  | 3.9    | 3.10   | 3.11   | 3.12   |
|------------------|:------:|:------:|:------:|:------:|
| linux (glibc) - x86    | ✅     | ✅     | ✅     | ✅     |
| linux (musl) - x86     | ✅     | ✅     | ✅     | ✅     |
| linux (glibc) - arm64  | ✅     | ✅     | ✅     | ✅     |
| linux (musl) - arm64   | ✅     | ✅     | ✅     | ✅     |
| OSX - arm64            | ✅     | ✅     | ✅     | ✅     |
| windows - x86          | ⚠️     | ⚠️     | ⚠️     | ⚠️     |
| windows - arm64        | ⚠️     | ⚠️     | ⚠️     | ⚠️     |



## TLDR:

Register at [x10 testnet](https://testnet.x10.exchange/) by connecting a supported Ethereum Wallet. 

Navigate to [Api Management](https://testnet.x10.exchange/api-management)
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


