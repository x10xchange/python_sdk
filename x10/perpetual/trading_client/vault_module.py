import decimal
from datetime import timedelta
from decimal import Decimal
from types import NoneType
from typing import Optional

from x10.errors import X10Error
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.amounts import HumanReadableAmount, StarkAmount
from x10.perpetual.assets import Asset, AssetModel
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.order_object_settlement import (
    calculate_order_settlement_expiration,
    hash_limit_order,
)
from x10.perpetual.orders import LimitOrderSettlementModel
from x10.perpetual.trading_client.account_module import AccountModule
from x10.perpetual.trading_client.base_module import BaseModule
from x10.perpetual.trading_client.info_module import InfoModule
from x10.utils.date import utc_now
from x10.utils.http import send_post_request
from x10.utils.model import SettlementSignatureModel, X10BaseModel
from x10.utils.nonce import generate_nonce

# Protects from an error on shares pricing fluctuations.
VAULT_SHARES_SLIPPAGE_PCT = Decimal("0.65")
COLLATERAL_ASSET_NAME = "USD"


class DepositRequestModel(X10BaseModel):
    from_account_id: int
    to_account_id: int
    collateral: Decimal
    shares: Decimal
    settlement: LimitOrderSettlementModel


class WithdrawRequestModel(X10BaseModel):
    from_account_id: int
    to_account_id: int
    collateral: Decimal
    shares: Decimal
    settlement: LimitOrderSettlementModel


class VaultModule(BaseModule):
    def __init__(
        self,
        endpoint_config: EndpointConfig,
        *,
        info_module: InfoModule,
        account_module: AccountModule,
        account: Optional[StarkPerpetualAccount],
        api_key: Optional[str] = None,
    ):
        super().__init__(endpoint_config, api_key=api_key)

        self._info_module = info_module
        self._account_module = account_module
        self._account = account

    async def get_vault_share_balance(self) -> Decimal:
        spot_balances = (await self._account_module.get_spot_balances()).data
        if spot_balances is None:
            raise X10Error("Failed to get spot balances")
        vault_asset_balances = filter(lambda b: b.asset == self._get_endpoint_config().vault_asset_name, spot_balances)
        total_vault_asset_balance = sum(map(lambda b: b.balance, vault_asset_balances), Decimal(0))
        return total_vault_asset_balance

    async def withdraw_from_vault(self, shares_amount: Decimal, collateral_amount: Decimal) -> None:
        assets = await self._info_module.get_assets_dict()
        account_info = (await self._account_module.get_account()).data

        assert account_info is not None

        position_id = account_info.l2_vault
        collateral_asset = assets[COLLATERAL_ASSET_NAME]
        vault_asset = assets[self._get_endpoint_config().vault_asset_name]
        settlement, collateral_amount_human, shares_amount_human = self.__create_limit_order(
            collateral_amount=collateral_amount,
            shares_amount=shares_amount,
            position_id=position_id,
            collateral_asset_model=collateral_asset,
            vault_asset_model=vault_asset,
            buying_shares=False,
        )
        withdraw_request = WithdrawRequestModel(
            from_account_id=account_info.id,
            to_account_id=account_info.id,
            collateral=abs(collateral_amount_human.value),
            shares=abs(shares_amount_human.value),
            settlement=settlement,
        )
        url = self._get_url("/vault/user/withdrawals")
        resp = await send_post_request(
            await self.get_session(),
            url,
            NoneType,
            json=withdraw_request.to_api_request_json(exclude_none=True),
            api_key=self._get_api_key(),
        )

        if resp.error is not None:
            raise X10Error(f"Withdraw error: {resp.error}")

    async def deposit_to_vault(self, amount: Decimal) -> None:
        account_info = (await self._account_module.get_account()).data
        assets = await self._info_module.get_assets_dict()
        vault_asset_price = (
            await self._info_module.get_asset_price(asset_name=self._get_endpoint_config().vault_asset_name)
        ).data

        assert account_info is not None
        assert vault_asset_price is not None

        position_id = account_info.l2_vault
        collateral_asset = assets[COLLATERAL_ASSET_NAME]
        vault_asset = assets[self._get_endpoint_config().vault_asset_name]
        vault_shares_expected = self.__calc_vault_shares_expected(
            amount,
            vault_asset_price,
            vault_asset.precision,
        )

        settlement, collateral_amount_human, shares_amount_human = self.__create_limit_order(
            collateral_amount=amount,
            shares_amount=vault_shares_expected,
            position_id=position_id,
            collateral_asset_model=collateral_asset,
            vault_asset_model=vault_asset,
            buying_shares=True,
        )
        deposit_request = DepositRequestModel(
            from_account_id=account_info.id,
            to_account_id=account_info.id,
            collateral=abs(collateral_amount_human.value),
            shares=abs(shares_amount_human.value),
            settlement=settlement,
        )

        url = self._get_url("/vault/user/deposits")
        resp = await send_post_request(
            await self.get_session(),
            url,
            NoneType,
            json=deposit_request.to_api_request_json(exclude_none=True),
            api_key=self._get_api_key(),
        )

        if resp.error is not None:
            raise X10Error(f"Deposit error: {resp.error}")

    def __create_limit_order(
        self,
        *,
        collateral_amount,
        shares_amount,
        position_id,
        collateral_asset_model: AssetModel,
        vault_asset_model: AssetModel,
        buying_shares=True,
    ):
        if self._account is None:
            raise X10Error("Stark account is required for vault investments")

        vault_asset = Asset.from_model(vault_asset_model)
        collateral_asset = Asset.from_model(collateral_asset_model)

        collateral_amount_human = HumanReadableAmount(
            asset=collateral_asset,
            value=-collateral_amount if buying_shares else collateral_amount,
        )

        shares_amount_human = HumanReadableAmount(
            asset=vault_asset,
            value=shares_amount if buying_shares else -shares_amount,
        )
        collateral_amount_stark = collateral_amount_human.to_stark_amount(decimal.Context(rounding=decimal.ROUND_UP))
        shares_amount_stark = shares_amount_human.to_stark_amount(decimal.Context(rounding=decimal.ROUND_UP))

        nonce = generate_nonce()
        expire_time = utc_now() + timedelta(hours=1)
        order_hash = hash_limit_order(
            amount_base=shares_amount_stark,
            amount_quote=collateral_amount_stark,
            max_fee=StarkAmount(0, collateral_asset),
            nonce=nonce,
            position_id=position_id,
            expiration_timestamp=expire_time,
            public_key=self._account.public_key,
            starknet_domain=self._get_endpoint_config().starknet_domain,
        )
        order_signature = self._account.sign(order_hash)

        settlement = LimitOrderSettlementModel(
            base_amount=shares_amount_stark.value,
            quote_amount=collateral_amount_stark.value,
            fee_amount=0,
            base_asset_id=int(vault_asset.settlement_external_id, 16),
            quote_asset_id=int(collateral_asset.settlement_external_id, 16),
            fee_asset_id=int(collateral_asset.settlement_external_id, 16),
            expiration_timestamp=calculate_order_settlement_expiration(expire_time),
            nonce=nonce,
            receiver_position_id=position_id,
            sender_position_id=position_id,
            signature=SettlementSignatureModel(r=order_signature[0], s=order_signature[1]),
        )

        return settlement, collateral_amount_human, shares_amount_human

    @staticmethod
    def __calc_vault_shares_expected(
        collateral_amount: Decimal, vault_asset_price: Decimal, vault_asset_precision: int
    ) -> Decimal:
        shares = collateral_amount / vault_asset_price * VAULT_SHARES_SLIPPAGE_PCT
        return shares.quantize(Decimal("10") ** -vault_asset_precision, rounding=decimal.ROUND_FLOOR)
