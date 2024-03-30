from dataclasses import dataclass
from decimal import Context, Decimal


@dataclass
class Asset:
    id: int
    name: str
    precision: int
    active: bool
    is_collateral: bool
    settlement_external_id: str
    settlement_resolution: int
    l1_external_id: str
    l1_resolution: int

    def convert_human_readable_to_stark_quantity(self, internal: Decimal, rounding_context: Context) -> int:
        return int(
            rounding_context.multiply(internal, Decimal(self.settlement_resolution)).to_integral(
                context=rounding_context
            )
        )

    def convert_stark_to_internal_quantity(self, stark: int) -> Decimal:
        return Decimal(stark) / Decimal(self.settlement_resolution)

    def convert_l1_quantity_to_internal_quantity(self, l1: int) -> Decimal:
        return Decimal(l1) / Decimal(self.l1_resolution)

    def convert_internal_quantity_to_l1_quantity(self, internal: Decimal) -> int:
        if not self.is_collateral:
            raise ValueError("Only collateral assets have an L1 representation")
        return int(internal * Decimal(self.l1_resolution))
