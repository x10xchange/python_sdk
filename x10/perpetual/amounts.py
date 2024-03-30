import decimal
from dataclasses import dataclass
from decimal import Decimal

from x10.perpetual.assets import Asset

ROUNDING_SELL_CONTEXT = decimal.Context(rounding=decimal.ROUND_DOWN)
ROUNDING_BUY_CONTEXT = decimal.Context(rounding=decimal.ROUND_UP)
ROUNDING_FEE_CONTEXT = decimal.Context(rounding=decimal.ROUND_UP)


@dataclass
class HumanReadableAmount:
    value: Decimal
    asset: Asset

    def to_l1_amount(self) -> "L1Amount":
        converted_value = self.asset.convert_internal_quantity_to_l1_quantity(self.value)
        return L1Amount(converted_value, self.asset)

    def to_stark_amount(self, rounding_context: decimal.Context) -> "StarkAmount":
        converted_value = self.asset.convert_human_readable_to_stark_quantity(self.value, rounding_context)
        return StarkAmount(converted_value, self.asset)


@dataclass
class L1Amount:
    value: int
    asset: Asset

    def to_internal_amount(self) -> HumanReadableAmount:
        converted_value = self.asset.convert_l1_quantity_to_internal_quantity(self.value)
        return HumanReadableAmount(converted_value, self.asset)


@dataclass
class StarkAmount:
    value: int
    asset: Asset

    def to_internal_amount(self) -> HumanReadableAmount:
        converted_value = self.asset.convert_stark_to_internal_quantity(self.value)
        return HumanReadableAmount(converted_value, self.asset)


@dataclass
class StarkOrderAmounts:
    collateral_amount_internal: HumanReadableAmount
    synthetic_amount_internal: HumanReadableAmount
    fee_amount_internal: HumanReadableAmount
    fee_rate: Decimal
    rounding_context: decimal.Context
