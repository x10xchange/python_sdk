from decimal import Decimal

from fast_stark_crypto import get_withdrawal_msg_hash

from x10.core.amount import InternalAmount, SettlementAsset
from x10.core.client_config import ClientConfig, StarknetDomain
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.base import SettlementSignatureModel
from x10.models.withdrawal import (
    StarkWithdrawalSettlementModel,
    TimestampModel,
    WithdrawalRequestModel,
)
from x10.utils.date import calc_settlement_expiration
from x10.utils.nonce import generate_nonce

SETTLEMENT_EXPIRATION_BUFFER_DAYS = 15


def create_withdrawal_object(
    *,
    amount: Decimal,
    asset: SettlementAsset,
    recipient_stark_address: str,
    stark_account: StarkPerpetualAccount,
    config: ClientConfig,
    account_id: int,
    chain_id: str,
    description: str | None = None,
    nonce: int | None = None,
    quote_id: str | None = None,
) -> WithdrawalRequestModel:
    expiration_timestamp = calc_settlement_expiration(SETTLEMENT_EXPIRATION_BUFFER_DAYS)
    stark_amount = InternalAmount(amount, asset).to_stark_amount()
    starknet_domain: StarknetDomain = config.signing.starknet_domain

    if nonce is None:
        nonce = generate_nonce()

    withdrawal_hash = get_withdrawal_msg_hash(
        recipient_hex=recipient_stark_address,
        position_id=stark_account.vault,
        collateral_id=int(asset.starkex_id, base=16),
        amount=stark_amount.value,
        expiration=expiration_timestamp,
        salt=nonce,
        user_public_key=stark_account.public_key,
        domain_name=starknet_domain.name,
        domain_version=starknet_domain.version,
        domain_chain_id=starknet_domain.chain_id,
        domain_revision=starknet_domain.revision,
    )

    (transfer_signature_r, transfer_signature_s) = stark_account.sign(withdrawal_hash)

    settlement = StarkWithdrawalSettlementModel(
        recipient=int(recipient_stark_address, 16),
        position_id=stark_account.vault,
        collateral_id=int(asset.starkex_id, base=16),
        amount=stark_amount.value,
        expiration=TimestampModel(seconds=expiration_timestamp),
        salt=nonce,
        signature=SettlementSignatureModel(
            r=transfer_signature_r,
            s=transfer_signature_s,
        ),
    )

    return WithdrawalRequestModel(
        account_id=account_id,
        amount=amount,
        description=description,
        settlement=settlement,
        chain_id=chain_id,
        quote_id=quote_id,
        asset="USD",
    )
