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

for more information see [placing an order example](examples/placed_order_example_simple.py)

## Modules

The SDK currently provides functionality across three main modules

### Order Management Module 
The order module is accessed using the account property of the trading client
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

#### `get_positions_history`
Fetches the historical positions of the user's account. It can filter the positions based on market names and position side.

```python
pass
```

#### `get_open_orders`
Fetches the open orders of the user's account. It can filter the orders based on market names, order type, and order side.

```python
    open_orders = await trading_client.account.get_open_orders()
    await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])
```

#### `get_orders_history`
Fetches the historical orders of the user's account. It can filter the orders based on market names, order type, and order side.

```python
pass
```

#### `get_trades`
Fetches the trades of the user's account. It can filter the trades based on market names, trade side, and trade type.

```python
pass
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

#### `update_leverage`
Updates the leverage for a specific market.

```python
    await trading_client.account.update_leverage(market_name="BTC-USD", leverage=Decimal("20.0"))
```

### Markets Info Module 
The markets module is accessed using the account property of the trading client
```python
trading_client.markets_info
```
TODO

## Contribution

Make sure you have [poetry](https://python-poetry.org/) installed.

- Clone the repository: `git@github.com:x10xchange/python-trading.git`
- Navigate to the project directory: `cd python-trading`
- Create a virtual environment: `poetry shell`
- Install dependencies: `poetry install`
- Update `examples/placed_order_example.py` with your credentials
- Run it: `python -m examples.placed_order_example`

Custom commands:
- `make format` - format code with `black`
- `make lint` - run `safety`, `black`, `flake8` and `mypy` checks
- `make test` - run tests


