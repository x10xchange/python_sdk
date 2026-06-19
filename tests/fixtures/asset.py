from decimal import Decimal

from x10.models.asset import (
    AssetModel,
    AssetOperationModel,
    AssetOperationStatus,
    AssetOperationType,
    AssetType,
)


def create_asset_operations():
    return [
        AssetOperationModel(
            id="1816814506626514944",
            type=AssetOperationType.TRANSFER,
            status=AssetOperationStatus.COMPLETED,
            amount=Decimal("-100.0000000000000000"),
            fee=Decimal("0"),
            asset=1,
            time=1721997307818,
            account_id=3004,
            counterparty_account_id=7349,
        ),
        AssetOperationModel(
            id="1813548171448147968",
            type=AssetOperationType.CLAIM,
            status=AssetOperationStatus.COMPLETED,
            amount=Decimal("100000.0000000000000000"),
            fee=Decimal("0"),
            asset=1,
            time=1721218552833,
            account_id=3004,
        ),
    ]


def get_asset_usd():
    return AssetModel(
        id=1,
        name="USD",
        symbol="USD",
        precision=6,
        is_active=True,
        is_collateral=True,
        starkex_id=0x1,
        starkex_resolution=1000000,
        l1_id="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        l1_resolution=1000000,
        version=3,
        type=AssetType.SPOT,
        can_be_used_as_collateral=True,
    )


def get_asset_xvs():
    return AssetModel(
        id=94,
        name="XVS",
        symbol="XVS",
        precision=6,
        is_active=True,
        is_collateral=False,
        starkex_id=0x07DB365513DF1EE2EB8FC2D157D4D1CBA3D4A2EF59B44DD3D61124C88B4F6084,
        starkex_resolution=1000000,
        l1_id="0x07DB365513Df1eE2Eb8fC2d157d4D1cBA3d4a2eF59b44Dd3D61124C88b4f6084",
        l1_resolution=1000000,
        version=6,
        type=AssetType.PERPETUAL,
        can_be_used_as_collateral=False,
    )
