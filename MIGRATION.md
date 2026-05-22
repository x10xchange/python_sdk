# Migration Guide

## 1.4.x -> 1.5.0 (REST / Onboarding / Stream clients)

- `x10.perpetual.trading_client.PerpetualTradingClient` has been replaced with
`x10.clients.rest.RestApiClient` (client has the same interface but new name reflects its purpose better).
- Leftover models were migrated to `x10.models.*`.
- Most of the dataclasses are immutable now.
- `markets_info` module has been merged into `info` module.
- `x10.perpetual.stream_client.PerpetualStreamClient` has been replaced with
  `x10.clients.stream.StreamClient` (same interface, renamed to match the `RestApiClient` naming convention).
- `UserClient` replaced by `OnboardingClient`, which accepts an account address and a sign-message callback instead of a raw L1 private key.
- `onboard_subaccount` error handling has changed. Previously, it silently recovered an existing sub-account (HTTP 409) by fetching it from `get_accounts()`. Now it raises `ValidationError` on conflict. Handle duplicates explicitly if you relied on the automatic recovery.
- Fixes https://github.com/x10xchange/python_sdk/issues/99.

---

## 1.3.x -> 1.4.0

- All data models have been moved from submodules under `x10/perpetual/*` and
`x10/utils/model.py` into a single, dedicated `x10.models` package. A small number of
classes were also renamed to follow the consistent `*Model` suffix convention.
- `StarkPerpetualAccount` (previously in `x10.perpetual.accounts`) has moved to `x10.core.stark_account`.
- The package now ships a `py.typed` marker (PEP 561), so mypy will now type-check against
the SDK's inline annotations by default.
- `x10.perpetual.configuration` has been **deleted**. All config types and pre-built instances now live in `x10.config`.
- `TESTNET_CONFIG` and `MAINNET_CONFIG` are now instances of the new `Config` dataclass (groups URLs, singing settings, defaults).
- Market names constants have been removed from `x10.config`. Define market name strings inline in your own code.
