import decimal
from decimal import Decimal
from types import NoneType
from typing import Optional

from x10.config import Config
from x10.core.stark_account import StarkPerpetualAccount
from x10.errors import ApiError, SdkValidationError
from x10.models.base import X10BaseModel
from x10.models.order import LimitOrderSettlementModel
from x10.perpetual.limit_order_object_settlement import create_order_settlement_data
from x10.perpetual.trading_client.account_module import AccountModule
from x10.perpetual.trading_client.base_module import BaseModule
from x10.perpetual.trading_client.info_module import InfoModule
from x10.utils.http import send_post_request

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
        config: Config,
        *,
        info_module: InfoModule,
        account_module: AccountModule,
        account: Optional[StarkPerpetualAccount] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(config, api_key=api_key)

        self._info_module = info_module
        self._account_module = account_module
        self._account = account

    async def get_vault_share_balance(self) -> Decimal:
        spot_balances = (await self._account_module.get_spot_balances()).data
        if spot_balances is None:
            raise SdkValidationError("Failed to get spot balances")
        vault_asset_balances = filter(lambda b: b.asset == self._get_endpoint_config().vault_asset_name, spot_balances)
        total_vault_asset_balance = sum(map(lambda b: b.balance, vault_asset_balances), Decimal(0))
        return total_vault_asset_balance

    async def deposit_to_vault(self, *, collateral_amount: Decimal) -> None:
        if self._account is None:
            raise SdkValidationError("Stark account is required for vault operations")

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
            collateral_amount,
            vault_asset_price,
            vault_asset.precision,
        )

        settlement, collateral_amount_human, shares_amount_human = create_order_settlement_data(
            quote_amount=collateral_amount,
            base_amount=vault_shares_expected,
            position_id=position_id,
            quote_asset_model=collateral_asset,
            base_asset_model=vault_asset,
            starknet_account=self._account,
            starknet_domain=self._get_endpoint_config().starknet_domain,
            is_buy=True,
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
            raise ApiError(f"Deposit error: {resp.error}")

    async def withdraw_from_vault(self, *, shares_amount: Decimal) -> None:
        if self._account is None:
            raise SdkValidationError("Stark account is required for vault operations")

        assets = await self._info_module.get_assets_dict()
        account_info = (await self._account_module.get_account()).data
        vault_asset_price = (
            await self._info_module.get_asset_price(asset_name=self._get_endpoint_config().vault_asset_name)
        ).data

        assert account_info is not None
        assert vault_asset_price is not None

        position_id = account_info.l2_vault
        collateral_asset = assets[COLLATERAL_ASSET_NAME]
        vault_asset = assets[self._get_endpoint_config().vault_asset_name]
        collateral_amount_expected = self.__calc_collateral_amount_expected(
            shares_amount,
            vault_asset_price,
            vault_asset.precision,
        )

        settlement, collateral_amount_human, shares_amount_human = create_order_settlement_data(
            quote_amount=collateral_amount_expected,
            base_amount=shares_amount,
            position_id=position_id,
            quote_asset_model=collateral_asset,
            base_asset_model=vault_asset,
            starknet_account=self._account,
            starknet_domain=self._get_endpoint_config().starknet_domain,
            is_buy=False,
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
            raise ApiError(f"Withdraw error: {resp.error}")

    @staticmethod
    def __calc_vault_shares_expected(
        collateral_amount: Decimal, vault_asset_price: Decimal, vault_asset_precision: int
    ) -> Decimal:
        shares = collateral_amount / vault_asset_price * VAULT_SHARES_SLIPPAGE_PCT
        return shares.quantize(Decimal("10") ** -vault_asset_precision, rounding=decimal.ROUND_FLOOR)

    @staticmethod
    def __calc_collateral_amount_expected(
        shares_amount: Decimal, vault_asset_price: Decimal, collateral_asset_precision: int
    ) -> Decimal:
        collateral_amount = shares_amount * vault_asset_price * VAULT_SHARES_SLIPPAGE_PCT
        return collateral_amount.quantize(Decimal("10") ** -collateral_asset_precision, rounding=decimal.ROUND_FLOOR)
