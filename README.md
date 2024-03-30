# X10

Python client for [X10 API](https://x101.docs.apiary.io).

Minimum Python version required to use this library is `3.10` (you can use [pyenv](https://github.com/pyenv/pyenv) to manage your Python versions easily).

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
