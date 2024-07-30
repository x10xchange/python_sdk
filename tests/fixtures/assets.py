from decimal import Decimal

from x10.perpetual.assets import AssetOperationModel


def create_asset_operations():
    return [
        AssetOperationModel(
            id="1816814506626514944",
            type="TRANSFER",
            status="COMPLETED",
            amount=Decimal("-100.0000000000000000"),
            fee=Decimal("0"),
            asset=1,
            time=1721997307818,
            account_id=3004,
            counterparty_account_id=7349,
        ),
        AssetOperationModel(
            id="1813548171448147968",
            type="CLAIM",
            status="COMPLETED",
            amount=Decimal("100000.0000000000000000"),
            fee=Decimal("0"),
            asset=1,
            time=1721218552833,
            account_id=3004,
        ),
    ]
