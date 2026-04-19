# Migration Guide

## 1.3.1 -> 1.4.0

- All data models have been moved from submodules under `x10/perpetual/*` and
`x10/utils/model.py` into a single, dedicated `x10.models` package. A small number of
classes were also renamed to follow the consistent `*Model` suffix convention.
- `StarkPerpetualAccount` (previously in `x10.perpetual.accounts`) has moved to `x10.core.stark_account`.
- The package now ships a `py.typed` marker (PEP 561), so mypy will now type-check against
the SDK's inline annotations by default.
