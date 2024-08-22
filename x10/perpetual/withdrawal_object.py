import math
from datetime import timedelta
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.withdrawals import PerpetualSlowWithdrawal, StarkWithdrawalSettlement
from x10.utils.date import utc_now
from x10.utils.model import SettlementSignatureModel
from x10.utils.starkex import generate_nonce, get_withdrawal_to_address_msg

SECONDS_IN_HOUR = 60 * 60


def calc_expiration_timestamp():
    expire_time = utc_now() + timedelta(days=15)
    expire_time_with_buffer = expire_time + timedelta(days=14)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    return expire_time_with_buffer_as_hours


def create_withdrawal_object(
    amount: Decimal,
    eth_address: str,
    stark_account: StarkPerpetualAccount,
    config: EndpointConfig,
    description: str | None = None,
) -> PerpetualSlowWithdrawal:
    expiration_timestamp = calc_expiration_timestamp()
    stark_amount = (amount.scaleb(config.collateral_decimals)).to_integral_exact()

    nonce = generate_nonce()
    withdrawal_hash = get_withdrawal_to_address_msg(
        asset_id_collateral=int(config.collateral_asset_on_chain_id, base=16),
        position_id=stark_account.vault,
        eth_address=eth_address,
        nonce=nonce,
        expiration_timestamp=expiration_timestamp,
        amount=int(stark_amount),
    )
    (withdrawal_signature_r, withdrawal_signature_s) = stark_account.sign(withdrawal_hash)

    settlement = StarkWithdrawalSettlement(
        amount=int(stark_amount),
        collateral_asset_id=int(config.collateral_asset_on_chain_id, base=16),
        eth_address=int(eth_address, base=16),
        expiration_timestamp=expiration_timestamp,
        nonce=nonce,
        position_id=stark_account.vault,
        public_key=stark_account.public_key,
        signature=SettlementSignatureModel(
            r=withdrawal_signature_r,
            s=withdrawal_signature_s,
        ),
    )

    return PerpetualSlowWithdrawal(amount=amount, settlement=settlement, description=description)
