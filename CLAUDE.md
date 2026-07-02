# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python SDK (`x10-python-trading-starknet`) for the Extended exchange API — a perpetuals DEX on Starknet.
Async-first (aiohttp/websockets), Pydantic v2 models, Python ≥3.10. Stark signing/hashing is delegated
to the `fast_stark_crypto` Rust wrapper. Published to PyPI via Poetry.

`starknet` is the default GIT branch.

## Commands

Dependency management is via Poetry (`poetry install`). All checks run through the Makefile:

```shell
make format   # isort (black profile) + black, line length 120, target py310
make lint     # black --check, flake8, mypy (examples/tests/x10)
make test     # tox: poetry install + pytest with coverage gate (--cov-fail-under=65, --forked)
```

Run tests directly (faster than tox):

```shell
poetry run pytest --forked tests/ --import-mode importlib
poetry run pytest --forked tests/clients/test_rest_api_client.py --import-mode importlib   # single file
poetry run pytest --forked tests/ -k test_get_markets --import-mode importlib              # single test
```

CI (`.github/workflows/code-checks.yml`) runs lint + tests on Python 3.10–3.13 for PRs targeting the `starknet` branch.

All checks and tests are expected to pass.

## Architecture

Everything lives under the `x10/` package:

- **`x10/config.py`** — `TESTNET_CONFIG` / `MAINNET_CONFIG` (`ClientConfig` frozen dataclasses bundling endpoints, 
  signing domain, defaults). Entry point for choosing an environment; `get_config_by_name("TESTNET"|"MAINNET")`.
- **`x10/core/`** — `ClientConfig` dataclasses, `EnvConfig` (reads `X10_` prefixed env vars),
  `StarkPerpetualAccount` (holds Stark keys + API key, signs message hashes), amount/decimal helpers.
- **`x10/clients/`** — one sub-package per client type:
  - `blocking/` — `BlockingTradingClient`, synchronous-style order placement built on REST + stream,
     waits for order status via account stream.
  - `onboarding/` — `OnboardingClient`; derives Stark keys from an Ethereum account via an EIP-712
    sign-message callback (it takes a callback, not a raw L1 private key for security).
  - `rest/` — `RestApiClient`, composed of feature modules (`info`, `account`, `orders`, `vault`, `testnet`, `builder`)
    exposed as properties. Each module extends `modules/base_module.py:BaseModule`, which owns
    the lazily-created shared `aiohttp.ClientSession`, config, and credential access. New REST endpoints
    go into the appropriate module (or a new module registered on the client).
  - `stream/` — `StreamClient`, one WebSocket connection per topic subscription,
    yields `WrappedStreamResponseModel[T]`.
  - `streamrpc/` — JSON-RPC-2.0-over-WebSocket client which supports multiple topics over a single connection
    (with auto-reconnect and resubscription on disconnect).
- **`x10/models/`** — Pydantic models. All extend `models/base.py:X10BaseModel`
  (frozen, camelCase wire aliases — see conventions below).
- **`x10/signing/`** — builds and Stark-signs settlement objects (orders, TP/SL, transfers, withdrawals, onboarding payloads).
  Order creation flows through `signing/order_object.py:create_order_object`, which hashes
  via the Starknet domain from `ClientConfig.signing` and signs with `StarkPerpetualAccount`.
- **`x10/tools/mcp/`** — experimental MCP server (optional `mcp` extra; `x10-mcp` script entry point).
- **`x10/utils/http.py`** — `WrappedApiResponseModel[T]` (envelope every REST response is parsed into),
  `get_url` helper for building URLs.

**`specs/`** — holds OpenAPI specs for the API.

**`examples/cases/`** — holds runnable examples (each loads `.env` via `EnvConfig.parse()` and follows the pattern shown in [README.md](./README.md)).

## Testing

- `pytest` with `pytest-asyncio` — async tests are marked `@pytest.mark.asyncio`.
- REST client tests spin up a local fake API with the `aiohttp_server` fixture,
  then point the client at it via `dataclasses.replace(TESTNET_CONFIG, endpoints=...)`.
  No network calls or mocking of the HTTP layer itself.
- Assertions use PyHamcrest (`assert_that`, `equal_to`, `has_length`), not bare `assert`.
- Shared fixtures live in `tests/conftest.py` and delegate to factory functions in `tests/fixtures/`
  (accounts, markets, orderbook/stream messages). Reuse these when testing anything market- or account-related.
- `freezegun` is available for time-sensitive signing tests (nonces, expirations, deterministic hashes in `tests/signing/`).
- Tox enforces 65% coverage and runs tests `--forked` (process isolation).

## Conventions

- **Models**: extend `X10BaseModel`. It is frozen (`ConfigDict(frozen=True)`) and auto-generates
  camelCase aliases for every snake_case field via `__init_subclass__` (`AliasChoices` accepts both snake and
  camel on validation; serialization is camelCase). Use `to_api_request_json()` when building
  request payloads — not `model_dump()` directly. Wrap hex-encoded ints with the `HexValue` annotated type.
- **Money/quantities are always `Decimal`**, never float.
- **Clients/modules** use name-mangled private attributes (`__config`, `__session`) with public `@property`
  accessors, and support `async with` (`close()`/`__aexit__` closes the aiohttp session).
- **Errors**: raise SDK types from `x10/errors.py` (`ValidationError`, `SdkError`, `NotSupportedError`, stream RPC errors) rather than builtins.
- Formatting: black + isort (black profile), line length 120; flake8 with bugbear; mypy runs with the pydantic plugin
  and strict init settings — keep new code fully typed.
- Breaking changes to the public API must be documented in [MIGRATION.md](./MIGRATION.md).
- Per [CONTRIBUTING.md](./CONTRIBUTING.md), the project doesn't accept PRs larger than ~500 LOC; keep changes scoped.
