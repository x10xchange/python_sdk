import math
import random
from datetime import datetime, timedelta
from typing import Callable, Literal, Optional

try:
    from fast_stark_crypto import pedersen_hash as ph_fast

    def pedersen_hash(first: int, second: int) -> int:
        return ph_fast(first, second)

except ImportError as e:
    from starkware.crypto.signature.signature import pedersen_hash as ph_slow

    print("WARNING: COULD NOT IMPORT RUST CRYPTO - USING SLOW PYTHON PEDERSEN IMPL {}", e.msg)

    def pedersen_hash(first: int, second: int) -> int:
        return ph_slow(first, second)


try:
    from fast_stark_crypto import sign as __sign_fast

    from starkware.crypto.signature.signature import generate_k_rfc6979

    def sign(private_key: int, msg_hash: int) -> tuple[int, int]:
        return __sign_fast(
            private_key=private_key, msg_hash=msg_hash, k=generate_k_rfc6979(msg_hash=msg_hash, priv_key=private_key)
        )

except ImportError as e:
    from starkware.crypto.signature.signature import sign as __sign_slow

    print("WARNING: COULD NOT IMPORT RUST CRYPTO - USING SLOW PYTHON SIGN IMPL {}", e.msg)

    def sign(private_key: int, msg_hash: int) -> tuple[int, int]:
        return __sign_slow(priv_key=private_key, msg_hash=msg_hash)


from x10.perpetual.amounts import ROUNDING_FEE_CONTEXT, StarkAmount, StarkOrderAmounts

LIMIT_ORDER_WITH_FEES = 3
TRANSFER = 4
CONDITIONAL_TRANSFER = 5
WITHDRAWAL_TO_ADDRESS = 7

Endianness = Literal["big", "little"]

HOURS_IN_DAY = 24
SETTLEMENT_BUFFER_HOURS = HOURS_IN_DAY * 7
SECONDS_IN_HOUR = 60 * 60


def build_condition(fact_registry_address: str, fact: bytes) -> int:
    # FIXME: Missing dep
    from web3 import Web3  # type: ignore

    """
    Creates a condition from a fact registry address and a fact.
    """
    condition_keccak = Web3.solidityKeccak(["address", "bytes32"], [fact_registry_address, fact])
    # Reduced to 250 LSB to be a field element.
    return from_bytes(condition_keccak) & (2**250 - 1)


def get_conditional_transfer_msg(
    asset_id: int,
    asset_id_fee: int,
    receiver_public_key: int,
    condition: int,
    sender_position_id: int,
    receiver_position_id: int,
    src_fee_position_id: int,
    nonce: int,
    amount: int,
    max_amount_fee: int,
    expiration_timestamp: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    assert 0 <= amount < 2**64
    assert 0 <= asset_id < 2**250
    assert 0 <= asset_id_fee < 2**250
    assert 0 <= condition < 2**251
    assert 0 <= expiration_timestamp < 2**32
    assert 0 <= src_fee_position_id < 2**64
    assert 0 <= max_amount_fee < 2**64
    assert 0 <= nonce < 2**32
    assert 0 <= receiver_position_id < 2**64
    assert 0 <= receiver_public_key < 2**251
    assert 0 <= sender_position_id < 2**64

    return get_conditional_transfer_msg_without_bounds(
        asset_id,
        asset_id_fee,
        receiver_public_key,
        condition,
        sender_position_id,
        receiver_position_id,
        src_fee_position_id,
        nonce,
        amount,
        max_amount_fee,
        expiration_timestamp,
        hash_function=hash_function,
    )


def get_conditional_transfer_msg_without_bounds(
    asset_id: int,
    asset_id_fee: int,
    receiver_public_key: int,
    condition: int,
    sender_position_id: int,
    receiver_position_id: int,
    src_fee_position_id: int,
    nonce: int,
    amount: int,
    max_amount_fee: int,
    expiration_timestamp: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    msg = hash_function(asset_id, asset_id_fee)
    msg = hash_function(msg, receiver_public_key)
    msg = hash_function(msg, condition)

    packed_message0 = sender_position_id
    packed_message0 = packed_message0 * 2**64 + receiver_position_id
    packed_message0 = packed_message0 * 2**64 + src_fee_position_id
    packed_message0 = packed_message0 * 2**32 + nonce
    msg = hash_function(msg, packed_message0)
    packed_message1 = CONDITIONAL_TRANSFER
    packed_message1 = packed_message1 * 2**64 + amount
    packed_message1 = packed_message1 * 2**64 + max_amount_fee
    packed_message1 = packed_message1 * 2**32 + expiration_timestamp
    packed_message1 = packed_message1 * 2**81  # Padding.
    return hash_function(msg, packed_message1)


def get_transfer_msg(
    asset_id: int,
    asset_id_fee: int,
    receiver_public_key: int,
    sender_position_id: int,
    receiver_position_id: int,
    src_fee_position_id: int,
    nonce: int,
    amount: int,
    max_amount_fee: int,
    expiration_timestamp: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    assert 0 <= amount < 2**64
    assert 0 <= asset_id < 2**250
    assert 0 <= asset_id_fee < 2**250
    assert 0 <= expiration_timestamp < 2**32
    assert 0 <= max_amount_fee < 2**64
    assert 0 <= nonce < 2**32
    assert 0 <= receiver_position_id < 2**64
    assert 0 <= receiver_public_key < 2**251
    assert 0 <= sender_position_id < 2**64
    assert 0 <= src_fee_position_id < 2**64

    return get_transfer_msg_without_bounds(
        asset_id,
        asset_id_fee,
        receiver_public_key,
        sender_position_id,
        receiver_position_id,
        src_fee_position_id,
        nonce,
        amount,
        max_amount_fee,
        expiration_timestamp,
        hash_function=hash_function,
    )


def get_transfer_msg_without_bounds(
    asset_id: int,
    asset_id_fee: int,
    receiver_public_key: int,
    sender_position_id: int,
    receiver_position_id: int,
    src_fee_position_id: int,
    nonce: int,
    amount: int,
    max_amount_fee: int,
    expiration_timestamp: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    msg = hash_function(asset_id, asset_id_fee)
    msg = hash_function(msg, receiver_public_key)

    packed_message0 = sender_position_id
    packed_message0 = packed_message0 * 2**64 + receiver_position_id
    packed_message0 = packed_message0 * 2**64 + src_fee_position_id
    packed_message0 = packed_message0 * 2**32 + nonce
    msg = hash_function(msg, packed_message0)
    packed_message1 = TRANSFER
    packed_message1 = packed_message1 * 2**64 + amount
    packed_message1 = packed_message1 * 2**64 + max_amount_fee
    packed_message1 = packed_message1 * 2**32 + expiration_timestamp
    packed_message1 = packed_message1 * 2**81  # Padding.
    return hash_function(msg, packed_message1)


def get_withdrawal_to_address_msg(
    asset_id_collateral: int,
    position_id: int,
    eth_address: str,
    nonce: int,
    expiration_timestamp: int,
    amount: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    assert 0 <= asset_id_collateral < 2**250
    assert 0 <= nonce < 2**32
    assert 0 <= position_id < 2**64
    assert 0 <= expiration_timestamp < 2**32
    assert 0 <= amount < 2**64
    assert 0 <= int(eth_address, 16) < 2**160

    return get_withdrawal_to_address_msg_without_bounds(
        asset_id_collateral,
        position_id,
        eth_address,
        nonce,
        expiration_timestamp,
        amount,
        hash_function=hash_function,
    )


def get_withdrawal_to_address_msg_without_bounds(
    asset_id_collateral: int,
    position_id: int,
    eth_address: str,
    nonce: int,
    expiration_timestamp: int,
    amount: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    eth_address_int = int(eth_address, 16)

    packed_message = WITHDRAWAL_TO_ADDRESS
    packed_message = packed_message * 2**64 + position_id
    packed_message = packed_message * 2**32 + nonce
    packed_message = packed_message * 2**64 + amount
    packed_message = packed_message * 2**32 + expiration_timestamp
    packed_message = packed_message * 2**49  # Padding.
    return hash_function(hash_function(asset_id_collateral, eth_address_int), packed_message)


def get_limit_order_msg(
    asset_id_synthetic: int,
    asset_id_collateral: int,
    is_buying_synthetic: int,
    asset_id_fee: int,
    amount_synthetic: int,
    amount_collateral: int,
    max_amount_fee: int,
    nonce: int,
    position_id: int,
    expiration_timestamp: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    # Synthetic asset IDs are generated by the exchange based on other crypto currency counterparts.
    assert 0 <= asset_id_synthetic < 2**128
    # Collateral asset ID is linked to a smart contract as part of its hash_function. Its range is
    # larger than synthetic asset IDs in order to reduce the chance of a collision of IDs.
    assert 0 <= asset_id_collateral < 2**250
    assert 0 <= asset_id_fee < 2**250
    assert 0 <= amount_synthetic < 2**64
    assert 0 <= amount_collateral < 2**64
    assert 0 <= max_amount_fee < 2**64
    assert 0 <= nonce < 2**32
    assert 0 <= position_id < 2**64
    assert 0 <= expiration_timestamp < 2**32

    return get_limit_order_msg_without_bounds(
        asset_id_synthetic,
        asset_id_collateral,
        is_buying_synthetic,
        asset_id_fee,
        amount_synthetic,
        amount_collateral,
        max_amount_fee,
        nonce,
        position_id,
        expiration_timestamp,
        hash_function=hash_function,
    )


def get_limit_order_msg_without_bounds(
    asset_id_synthetic: int,
    asset_id_collateral: int,
    is_buying_synthetic: int,
    asset_id_fee: int,
    amount_synthetic: int,
    amount_collateral: int,
    max_amount_fee: int,
    nonce: int,
    position_id: int,
    expiration_timestamp: int,
    hash_function: Callable[[int, int], int] = pedersen_hash,
) -> int:
    if is_buying_synthetic:
        asset_id_sell, asset_id_buy = asset_id_collateral, asset_id_synthetic
        amount_sell, amount_buy = amount_collateral, amount_synthetic
    else:
        asset_id_sell, asset_id_buy = asset_id_synthetic, asset_id_collateral
        amount_sell, amount_buy = amount_synthetic, amount_collateral

    msg = hash_function(asset_id_sell, asset_id_buy)
    msg = hash_function(msg, asset_id_fee)
    packed_message0 = amount_sell
    packed_message0 = packed_message0 * 2**64 + amount_buy
    packed_message0 = packed_message0 * 2**64 + max_amount_fee
    packed_message0 = packed_message0 * 2**32 + nonce
    msg = hash_function(msg, packed_message0)
    packed_message1 = LIMIT_ORDER_WITH_FEES
    packed_message1 = packed_message1 * 2**64 + position_id
    packed_message1 = packed_message1 * 2**64 + position_id
    packed_message1 = packed_message1 * 2**64 + position_id
    packed_message1 = packed_message1 * 2**32 + expiration_timestamp
    packed_message1 = packed_message1 * 2**17  # Padding.
    return hash_function(msg, packed_message1)


#####################################################################################
# get_price_msg: gets as input:                                                     #
#   oracle: a 40-bit number, describes the oracle (e.g., hex encoding of "Maker")   #
#   price: a 120-bit number                                                         #
#   asset: a 211-bit number                                                         #
#   timestamp: a 32 bit number, represents seconds since Unix epoch                 #
# Outputs a number which is less than FIELD_PRIME, which can be used as data        #
# to sign on in the sign method. This number is obtained by applying pedersen hash  #
# on the following two numbers:                                                     #
#                                                                                   #
# first number:                                                                     #
# --------------------------------------------------------------------------------- #
# | asset_name (rest of the number)  - 211 bits       |   oracle_name (40 bits)   | #
# --------------------------------------------------------------------------------- #
#                                                                                   #
# second number:                                                                    #
# --------------------------------------------------------------------------------- #
# | 0 (92 bits)         | price (120 bits)              |   timestamp (32 bits)   | #
# --------------------------------------------------------------------------------- #
#####################################################################################


def get_price_msg(
    oracle_name: int,
    asset_pair: int,
    timestamp: int,
    price: int,
    hash_function=pedersen_hash,
):
    assert 0 <= oracle_name < 2**40
    assert 0 <= asset_pair < 2**128
    assert 0 <= timestamp < 2**32
    assert 0 <= price < 2**120

    # The first number to hash_function is the oracle name (e.g., Maker) in the 40 LSB, then the
    # asset name.
    first_number = (asset_pair << 40) + oracle_name

    # The second number is timestamp in the 32 LSB, then the price.
    second_number = (price << 32) + timestamp

    return hash_function(first_number, second_number)


def from_bytes(
    value: bytes,
    byte_order: Optional[Endianness] = None,
    signed: Optional[bool] = None,
) -> int:
    """
    Converts the given bytes object (parsed according to the given byte order) to an integer.
    Default byte order is 'big'.
    """
    if byte_order is None:
        byte_order = "big"

    if signed is None:
        signed = False

    return int.from_bytes(value, byteorder=byte_order, signed=signed)


def hash_order(
    amounts: StarkOrderAmounts,
    is_buying_synthetic: bool,
    nonce: int,
    position_id: int,
    expiration_timestamp: datetime,
) -> int:
    amount_synthetic: StarkAmount = amounts.synthetic_amount_internal.to_stark_amount(
        rounding_context=amounts.rounding_context
    )
    amount_collateral: StarkAmount = amounts.collateral_amount_internal.to_stark_amount(
        rounding_context=amounts.rounding_context
    )
    max_fee: StarkAmount = amounts.fee_amount_internal.to_stark_amount(rounding_context=ROUNDING_FEE_CONTEXT)
    synthetic_asset = amount_synthetic.asset
    collateral_asset = amount_collateral.asset

    expire_time_with_buffer = expiration_timestamp + timedelta(days=7)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    return get_limit_order_msg(
        int(synthetic_asset.settlement_external_id, base=16),
        int(collateral_asset.settlement_external_id, base=16),
        1 if is_buying_synthetic else 0,
        int(collateral_asset.settlement_external_id, base=16),
        amount_synthetic.value,
        amount_collateral.value,
        max_fee.value,
        nonce,
        position_id,
        expire_time_with_buffer_as_hours,
        pedersen_hash,
    )


def generate_nonce():
    # Aligned with the JS implementation (2^31 as the upper bound, not 2^32).
    # https://github.com/starkware-libs/starkware-crypto-utils/blob/dev/src/js/signature.ts#L327
    return random.randint(0, 2**31 - 1)
