from decimal import Decimal
from typing import Optional

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide, PerpetualOrderModel, PlacedOrderModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import send_delete_request, send_post_request
from x10.utils.log import get_logger
from x10.utils.model import EmptyModel, X10BaseModel

LOGGER = get_logger(__name__)


class _MassCancelRequestModel(X10BaseModel):
    order_ids: Optional[list[int]]
    external_order_ids: Optional[list[str]]
    market_ids: Optional[list[int]]
    cancel_all: Optional[bool]


class OrderManagementModule(BaseModule):
    @staticmethod
    async def create_order_object(
        *,
        account: StarkPerpetualAccount,
        market: MarketModel,
        amount_of_synthetic: Decimal,
        price: Decimal,
        side: OrderSide,
    ):
        return await create_order_object(
            account=account,
            market=market,
            amount_of_synthetic=amount_of_synthetic,
            price=price,
            side=side,
        )

    def place_order(self, order: PerpetualOrderModel):
        """
        Placed new order on the exchange.

        :param order: Order object created by `create_order_object` method.

        https://x101.docs.apiary.io/#reference/0/order-managment/create-order
        """
        LOGGER.debug("Placing an order: id=%s", order.id)

        url = self._get_url("/user/order")
        return send_post_request(url, PlacedOrderModel, json=order.to_api_request_json(), api_key=self._get_api_key())

    def cancel_order(self, order_id: int):
        """
        https://x101.docs.apiary.io/#reference/0/order-managment/cancel-order
        """

        url = self._get_url("/user/order/<order_id>", order_id=order_id)
        return send_delete_request(url, EmptyModel, api_key=self._get_api_key(), idempotent=True, retry=True)

    def mass_cancel(
        self,
        *,
        order_ids: Optional[list[int]] = None,
        external_order_ids: Optional[list[str]] = None,
        market_ids: Optional[list[int]] = None,
        cancel_all: Optional[bool] = False,
    ):
        """
        https://x101.docs.apiary.io/#reference/0/order-managment/mass-cancel
        """

        url = self._get_url("/user/order/massCancel")
        request_model = _MassCancelRequestModel(
            order_ids=order_ids,
            external_order_ids=external_order_ids,
            market_ids=market_ids,
            cancel_all=cancel_all,
        )
        return send_post_request(
            url, EmptyModel, json=request_model.to_api_request_json(exclude_none=True), api_key=self._get_api_key()
        )
