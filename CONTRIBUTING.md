# Contributing to Extended Python SDK

Thanks for showing interest to contribute to Extended Python SDK!

## Discuss changes before starting to work on them

> [!WARNING]
> Please note that SDK is under an active development / reworking.

Please first discuss the change you wish to make by creating an issue or reaching out to us in the
[devs-api-trading](https://discord.com/channels/1193905940076953660/1269958891819765842) Discord channel
before making a change. This helps everyone to be on the same page and makes the chances of your contributions
being integrated into the project much higher. We do not accept PRs larger than 500 LOC at the moment,
as we are still working on the structure of the SDK and its core features. If we identify misalignments between
your PR and our roadmap / vision, it might be easier for us to push our own implementation to avoid
unnecessary iterations.

## License

By contributing to this project, you agree that your contributions will be licensed under its [LICENSE](LICENSE).

## Env setup

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
