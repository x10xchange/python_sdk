import decimal
from dataclasses import dataclass
from decimal import Decimal

from x10.errors import ValidationError

ROUNDING_SELL_CONTEXT = decimal.Context(rounding=decimal.ROUND_DOWN)
ROUNDING_BUY_CONTEXT = decimal.Context(rounding=decimal.ROUND_UP)
ROUNDING_FEE_CONTEXT = decimal.Context(rounding=decimal.ROUND_UP)


@dataclass(frozen=True)
class SettlementAsset:
    """
    Subset of `AssetModel` properties to be used for settlement without needing
    to depend on the full asset model.
    """

    name: str
    precision: int
    is_collateral: bool
    starkex_id: str
    starkex_resolution: int
    l1_id: str | None = None
    l1_resolution: int | None = None


@dataclass(frozen=True)
class InternalAmount:
    """
    Amount representation (human-readable) used for internal calculations
    and as the source of truth for conversions to other representations.
    """

    value: Decimal
    asset: SettlementAsset

    def to_l1_amount(self) -> "L1Amount":
        if not self.asset.is_collateral or not self.asset.l1_resolution:
            raise ValidationError(
                f"Not supported or missing for {self.asset.name}. Only collateral assets have an L1 representation."
            )

        converted_value = int(self.value * Decimal(self.asset.l1_resolution))
        return L1Amount(converted_value, self.asset)

    def to_stark_amount(self, rounding_context: decimal.Context) -> "StarkAmount":
        converted_value = int(
            rounding_context.multiply(self.value, Decimal(self.asset.starkex_resolution)).to_integral(
                context=rounding_context
            )
        )
        return StarkAmount(converted_value, self.asset)


@dataclass(frozen=True)
class L1Amount:
    value: int
    asset: SettlementAsset

    def to_internal_amount(self) -> InternalAmount:
        if not self.asset.is_collateral or not self.asset.l1_resolution:
            raise ValidationError(
                f"Not supported or missing for {self.asset.name}. Only collateral assets have an L1 representation."
            )

        converted_value = Decimal(self.value) / Decimal(self.asset.l1_resolution)
        return InternalAmount(converted_value, self.asset)


@dataclass(frozen=True)
class StarkAmount:
    value: int
    asset: SettlementAsset

    def negate(self) -> "StarkAmount":
        return StarkAmount(-self.value, self.asset)

    def to_internal_amount(self) -> InternalAmount:
        converted_value = Decimal(self.value) / Decimal(self.asset.starkex_resolution)
        return InternalAmount(converted_value, self.asset)
