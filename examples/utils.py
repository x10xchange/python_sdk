from decimal import Decimal

from x10.perpetual.markets import TradingConfigModel


def get_adjust_price_by_pct(config: TradingConfigModel):
    def adjust_price_by_pct(price: Decimal, pct: int):
        return config.round_price(price + price * Decimal(pct) / 100)

    return adjust_price_by_pct
