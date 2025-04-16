import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional, Tuple

from fast_stark_crypto import get_order_msg_hash

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.amounts import (
    ROUNDING_BUY_CONTEXT,
    ROUNDING_FEE_CONTEXT,
    ROUNDING_SELL_CONTEXT,
    HumanReadableAmount,
    StarkAmount,
)
from x10.perpetual.configuration import StarknetDomain
from x10.perpetual.fees import DEFAULT_FEES, TradingFeeModel
from x10.perpetual.markets import MarketModel
from x10.perpetual.orders import (
    OrderSide,
    OrderType,
    PerpetualOrderModel,
    SelfTradeProtectionLevel,
    SettlementSignatureModel,
    StarkDebuggingOrderAmountsModel,
    StarkSettlementModel,
    TimeInForce,
)
from x10.utils.date import to_epoch_millis, utc_now
from x10.utils.starkex import generate_nonce


def create_order_object(
    account: StarkPerpetualAccount,
    market: MarketModel,
    amount_of_synthetic: Decimal,
    price: Decimal,
    side: OrderSide,
    starknet_domain: StarknetDomain,
    post_only: bool = False,
    previous_order_id: Optional[str] = None,
    expire_time: Optional[datetime] = None,
    order_external_id: Optional[str] = None,
    time_in_force: TimeInForce = TimeInForce.GTT,
    self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
    nonce: Optional[int] = None,
) -> PerpetualOrderModel:
    """
    Creates an order object to be placed on the exchange using the `place_order` method.
    """

    if expire_time is None:
        expire_time = utc_now() + timedelta(hours=1)

    fees = account.trading_fee.get(market.name, DEFAULT_FEES)

    return __create_order_object(
        market=market,
        synthetic_amount=amount_of_synthetic,
        price=price,
        side=side,
        collateral_position_id=account.vault,
        fees=fees,
        signer=account.sign,
        public_key=account.public_key,
        exact_only=False,
        expire_time=expire_time,
        post_only=post_only,
        previous_order_external_id=previous_order_id,
        order_external_id=order_external_id,
        time_in_force=time_in_force,
        self_trade_protection_level=self_trade_protection_level,
        starknet_domain=starknet_domain,
        nonce=nonce,
    )


def __create_order_object(
    market: MarketModel,
    synthetic_amount: Decimal,
    price: Decimal,
    side: OrderSide,
    collateral_position_id: int,
    fees: TradingFeeModel,
    signer: Callable[[int], Tuple[int, int]],
    public_key: int,
    starknet_domain: StarknetDomain,
    exact_only: bool = False,
    expire_time: Optional[datetime] = None,
    post_only: bool = False,
    previous_order_external_id: Optional[str] = None,
    order_external_id: Optional[str] = None,
    time_in_force: TimeInForce = TimeInForce.GTT,
    self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
    nonce: Optional[int] = None,
) -> PerpetualOrderModel:
    if exact_only:
        raise NotImplementedError("`exact_only` option is not supported yet")

    if expire_time is None:
        raise ValueError("`expire_time` must be provided")
    if nonce is None:
        nonce = generate_nonce()
    is_buying_synthetic = side == OrderSide.BUY
    rounding_context = ROUNDING_BUY_CONTEXT if is_buying_synthetic else ROUNDING_SELL_CONTEXT

    collateral_amount_human = HumanReadableAmount(synthetic_amount * price, market.collateral_asset)
    synthetic_amount_human = HumanReadableAmount(synthetic_amount, market.synthetic_asset)
    fee_amount_human = HumanReadableAmount(
        fees.taker_fee_rate * collateral_amount_human.value,
        market.collateral_asset,
    )
    fee_rate = fees.taker_fee_rate

    stark_collateral_amount: StarkAmount = collateral_amount_human.to_stark_amount(rounding_context=rounding_context)
    stark_synthetic_amount: StarkAmount = synthetic_amount_human.to_stark_amount(rounding_context=rounding_context)
    stark_fee_amount: StarkAmount = fee_amount_human.to_stark_amount(rounding_context=ROUNDING_FEE_CONTEXT)

    if is_buying_synthetic:
        stark_collateral_amount = stark_collateral_amount.negate()
    else:
        stark_synthetic_amount = stark_synthetic_amount.negate()

    debugging_amounts = StarkDebuggingOrderAmountsModel(
        collateral_amount=Decimal(stark_collateral_amount.value),
        fee_amount=Decimal(stark_fee_amount.value),
        synthetic_amount=Decimal(stark_synthetic_amount.value),
    )

    order_hash = hash_order(
        amount_synthetic=stark_synthetic_amount,
        amount_collateral=stark_collateral_amount,
        max_fee=stark_fee_amount,
        nonce=nonce,
        position_id=collateral_position_id,
        expiration_timestamp=expire_time,
        public_key=public_key,
        starknet_domain=starknet_domain,
    )

    (order_signature_r, order_signature_s) = signer(order_hash)
    settlement = StarkSettlementModel(
        signature=SettlementSignatureModel(r=order_signature_r, s=order_signature_s),
        stark_key=public_key,
        collateral_position=Decimal(collateral_position_id),
    )

    order_id = str(order_hash) if order_external_id is None else order_external_id
    order = PerpetualOrderModel(
        id=order_id,
        market=market.name,
        type=OrderType.LIMIT,
        side=side,
        qty=synthetic_amount_human.value,
        price=price,
        post_only=post_only,
        time_in_force=time_in_force,
        expiry_epoch_millis=to_epoch_millis(expire_time),
        fee=fee_rate,
        self_trade_protection_level=self_trade_protection_level,
        nonce=Decimal(nonce),
        cancel_id=previous_order_external_id,
        settlement=settlement,
        debugging_amounts=debugging_amounts,
    )

    return order


def hash_order(
    amount_synthetic: StarkAmount,
    amount_collateral: StarkAmount,
    max_fee: StarkAmount,
    nonce: int,
    position_id: int,
    expiration_timestamp: datetime,
    public_key: int,
    starknet_domain: StarknetDomain,
) -> int:
    synthetic_asset = amount_synthetic.asset
    collateral_asset = amount_collateral.asset

    expire_time_with_buffer = expiration_timestamp + timedelta(days=14)
    expire_time_as_seconds = math.ceil(expire_time_with_buffer.timestamp())

    return get_order_msg_hash(
        position_id=position_id,
        base_asset_id=int(synthetic_asset.settlement_external_id, 16),
        base_amount=amount_synthetic.value,
        quote_asset_id=int(collateral_asset.settlement_external_id, 16),
        quote_amount=amount_collateral.value,
        fee_amount=max_fee.value,
        fee_asset_id=int(collateral_asset.settlement_external_id, 16),
        expiration=expire_time_as_seconds,
        salt=nonce,
        user_public_key=public_key,
        domain_name=starknet_domain.name,
        domain_version=starknet_domain.version,
        domain_chain_id=starknet_domain.chain_id,
        domain_revision=starknet_domain.revision,
    )
