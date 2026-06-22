from decimal import Decimal

from fast_stark_crypto import get_transfer_msg_hash

from x10.core.client_config import ClientConfig, StarknetDomain
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.base import SettlementSignatureModel
from x10.models.transfer import (
    OnChainPerpetualTransferModel,
    StarkTransferSettlementModel,
)
from x10.utils.date import calc_settlement_expiration
from x10.utils.nonce import generate_nonce

SETTLEMENT_EXPIRATION_BUFFER_DAYS = 21


def create_transfer_object(
    *,
    from_vault: int,
    to_vault: int,
    to_l2_public_key: int,
    amount: Decimal,
    asset_id: str,
    config: ClientConfig,
    stark_account: StarkPerpetualAccount,
    nonce: int | None = None,
) -> OnChainPerpetualTransferModel:
    expiration_timestamp = calc_settlement_expiration(SETTLEMENT_EXPIRATION_BUFFER_DAYS)
    scaled_amount = amount.scaleb(config.endpoints.collateral_decimals)
    stark_amount = scaled_amount.to_integral_exact()
    starknet_domain: StarknetDomain = config.signing.starknet_domain

    if nonce is None:
        nonce = generate_nonce()

    transfer_hash = get_transfer_msg_hash(
        recipient_position_id=to_vault,
        sender_position_id=from_vault,
        collateral_id=int(asset_id, 16),
        amount=int(stark_amount),
        expiration=expiration_timestamp,
        salt=nonce,
        user_public_key=stark_account.public_key,
        domain_name=starknet_domain.name,
        domain_version=starknet_domain.version,
        domain_chain_id=starknet_domain.chain_id,
        domain_revision=starknet_domain.revision,
    )

    (transfer_signature_r, transfer_signature_s) = stark_account.sign(transfer_hash)
    settlement = StarkTransferSettlementModel(
        amount=int(stark_amount),
        asset_id=int(asset_id, base=16),
        expiration_timestamp=expiration_timestamp,
        nonce=nonce,
        receiver_position_id=to_vault,
        receiver_public_key=to_l2_public_key,
        sender_position_id=from_vault,
        sender_public_key=stark_account.public_key,
        signature=SettlementSignatureModel(r=transfer_signature_r, s=transfer_signature_s),
    )

    return OnChainPerpetualTransferModel(
        from_vault=from_vault,
        to_vault=to_vault,
        amount=amount,
        settlement=settlement,
        transferred_asset=asset_id,
    )
