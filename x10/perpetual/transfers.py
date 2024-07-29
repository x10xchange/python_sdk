# FIXME
from decimal import Decimal

from x10.perpetual.orders import SignatureModel
from x10.utils.model import X10BaseModel, HexValue


# import { addDays } from 'date-fns'
#
# import type { CryptoCurrencyCollateralCode } from '@x10/lib-core/config'
# import { checkRequired, Long, type Decimal } from '@x10/lib-core/utils'
#
# import { calcStarkExpiration } from '../utils/calc-stark-expiration'
# import { generateNonce } from '../utils/generate-nonce'
# import { StarkTransferSettlement } from './stark-transfer-settlement'
# import type { TransferContext } from './types'
#
# const TRANSFER_EXPIRATION_DAYS = 7
#
# export class StarkTransfer {
#   private readonly fromAccountId: Long
#   private readonly toAccountId: Long
#   private readonly amount: Decimal
#   private readonly transferredAsset: CryptoCurrencyCollateralCode
#   private readonly settlement: StarkTransferSettlement
#
#   private constructor({
#     fromAccountId,
#     toAccountId,
#     amount,
#     transferredAsset,
#     settlement,
#   }: {
#     fromAccountId: Long
#     toAccountId: Long
#     amount: Decimal
#     transferredAsset: CryptoCurrencyCollateralCode
#     settlement: StarkTransferSettlement
#   }) {
#     this.fromAccountId = fromAccountId
#     this.toAccountId = toAccountId
#     this.amount = amount
#     this.transferredAsset = transferredAsset
#     this.settlement = settlement
#   }
#
#   toJSON() {
#     return {
#       fromAccount: this.fromAccountId.toString(10),
#       toAccount: this.toAccountId.toString(10),
#       amount: this.amount.toString(10),
#       transferredAsset: this.transferredAsset,
#       settlement: this.settlement.toJSON(),
#     }
#   }
#
#   static create({
#     fromAccountId,
#     toAccountId,
#     amount,
#     transferredAsset,
#     ctx,
#   }: {
#     fromAccountId: Long
#     toAccountId: Long
#     amount: Decimal
#     transferredAsset: CryptoCurrencyCollateralCode
#     ctx: TransferContext
#   }) {
#     const fromAccount = checkRequired(
#       ctx.accounts.find((account) => account.accountId.eq(fromAccountId)),
#       'fromAccount',
#     )
#     const toAccount = checkRequired(
#       ctx.accounts.find((account) => account.accountId.eq(toAccountId)),
#       'toAccount',
#     )
#     const expiryEpochMillis = addDays(new Date(), TRANSFER_EXPIRATION_DAYS).getTime()
#     const starkAmount = amount
#       .times(ctx.l2Config.collateralResolution)
#       .toIntegerValueExact()
#
#     return new StarkTransfer({
#       fromAccountId,
#       toAccountId,
#       amount,
#       transferredAsset,
#       settlement: StarkTransferSettlement.create({
#         amount: starkAmount,
#         assetId: ctx.l2Config.collateralId,
#         expirationTimestamp: calcStarkExpiration(expiryEpochMillis),
#         nonce: Long(generateNonce()),
#         receiverPositionId: Long(toAccount.l2Vault),
#         receiverPublicKey: toAccount.l2Key,
#         senderPositionId: Long(fromAccount.l2Vault),
#         senderPublicKey: fromAccount.l2Key,
#         starkPrivateKey: ctx.starkPrivateKey,
#       }),
#     })
#   }
# }


class StarkTransferSettlement(X10BaseModel):
    amount: int
    asset_id: HexValue
    expiration_timestamp: int
    nonce: int
    receiver_position_id: int
    receiver_public_key: HexValue
    sender_position_id: int
    sender_public_key: HexValue
    signature: SignatureModel


class PerpetualTransferModel(X10BaseModel):
    from_account: int
    to_account: int
    amount: Decimal
    transferred_asset: str
    settlement: StarkTransferSettlement


"""
{"fromAccount":"3004","toAccount":"7349","amount":"100","transferredAsset":"USD","settlement":{"amount":"100000000","assetId":"0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054","expirationTimestamp":478669,"nonce":"1281858528","receiverPositionId":"104350","receiverPublicKey":"0x3895139a98a6168dc8b0db251bcd0e6dcf97fd1e96f7a87d9bd3f341753a844","senderPositionId":"100005","senderPublicKey":"0x3895139a98a6168dc8b0db251bcd0e6dcf97fd1e96f7a87d9bd3f341753a844","signature":{"r":"6564e71233f3c24d19d1915781f48ba1b7c54c4c3286cea3cdbe708ce3ce849","s":"385e5794681760688d57bc01f41592cd7f04759eb76790998e407e519f06d18"}}}
"""

"""
{
    "status": "OK",
    "data": {
        "validSignature": true,
        "id": 1816814506613424128
    }
}
"""