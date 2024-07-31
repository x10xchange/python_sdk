import math
from datetime import timedelta
from decimal import Decimal
from typing import List

from x10.perpetual.accounts import AccountModel, StarkPerpetualAccount
from x10.perpetual.markets import MarketModel
from x10.perpetual.withdrawals import (
    PerpetualWithdrawalModel,
    StarkWithdrawalSettlement,
)
from x10.utils.date import utc_now
from x10.utils.model import SettlementSignatureModel
from x10.utils.starkex import generate_nonce, get_withdrawal_to_address_msg

SECONDS_IN_HOUR = 60 * 60


def find_account_by_id(accounts: List[AccountModel], account_id: int):
    return next((account for account in accounts if account.account_id == account_id), None)


def calc_expiration_timestamp():
    expire_time = utc_now() + timedelta(days=15)
    expire_time_with_buffer = expire_time + timedelta(days=7)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    return expire_time_with_buffer_as_hours


def create_withdrawal_object(
    account_id: int,
    amount: Decimal,
    asset: str,
    eth_address: str,
    stark_account: StarkPerpetualAccount,
    accounts: List[AccountModel],
    market: MarketModel,
):
    account = find_account_by_id(accounts, account_id)

    expiration_timestamp = calc_expiration_timestamp()
    stark_amount = (amount * market.collateral_asset.settlement_resolution).to_integral_exact()

    withdrawal_hash = get_withdrawal_to_address_msg(
        asset_id_collateral=int(market.l2_config.collateral_id, base=16),
        position_id=int(account.l2_vault),
        eth_address=eth_address,
        nonce=generate_nonce(),
        expiration_timestamp=expiration_timestamp,
        amount=int(stark_amount),
    )
    (withdrawal_signature_r, withdrawal_signature_s) = stark_account.sign(withdrawal_hash)

    settlement = StarkWithdrawalSettlement(
        amount=int(stark_amount),
        collateral_asset_id=int(market.l2_config.collateral_id, base=16),
        eth_address=int(eth_address, base=16),
        expiration_timestamp=expiration_timestamp,
        nonce=generate_nonce(),
        position_id=int(account.l2_vault),
        public_key=int(account.l2_key, base=16),
        signature=SettlementSignatureModel(
            r=withdrawal_signature_r,
            s=withdrawal_signature_s,
        ),
    )

    return PerpetualWithdrawalModel(
        account_id=account_id,
        amount=amount,
        asset=asset,
        settlement=settlement,
    )
