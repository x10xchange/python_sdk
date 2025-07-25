from typing import List, Optional

from x10.perpetual.orders import PerpetualOrderModel, PlacedOrderModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import send_delete_request, send_post_request
from x10.utils.log import get_logger
from x10.utils.model import EmptyModel, X10BaseModel

LOGGER = get_logger(__name__)


class _MassCancelRequestModel(X10BaseModel):
    order_ids: Optional[List[int]] = None
    external_order_ids: Optional[List[str]] = None
    markets: Optional[List[str]] = None
    cancel_all: Optional[bool] = None


class OrderManagementModule(BaseModule):
    async def place_order(self, order: PerpetualOrderModel):
        """
        Placed new order on the exchange.

        :param order: Order object created by `create_order_object` method.

        https://api.docs.extended.exchange/#create-order
        """
        LOGGER.debug("Placing an order: id=%s", order.id)

        url = self._get_url("/user/order")
        response = await send_post_request(
            await self.get_session(),
            url,
            PlacedOrderModel,
            json=order.to_api_request_json(),
            api_key=self._get_api_key(),
        )
        return response

    async def cancel_order(self, order_id: int):
        """
        https://api.docs.extended.exchange/#cancel-order
        """

        url = self._get_url("/user/order/<order_id>", order_id=order_id)
        return await send_delete_request(await self.get_session(), url, EmptyModel, api_key=self._get_api_key())

    async def cancel_order_by_external_id(self, order_external_id: str):
        """
        https://api.docs.extended.exchange/#cancel-order
        """

        url = self._get_url("/user/order", query={"externalId": order_external_id})
        return await send_delete_request(await self.get_session(), url, EmptyModel, api_key=self._get_api_key())

    async def mass_cancel(
        self,
        *,
        order_ids: Optional[List[int]] = None,
        external_order_ids: Optional[List[str]] = None,
        markets: Optional[List[str]] = None,
        cancel_all: Optional[bool] = False,
    ):
        """
        https://api.docs.extended.exchange/#mass-cancel
        """

        url = self._get_url("/user/order/massCancel")
        request_model = _MassCancelRequestModel(
            order_ids=order_ids,
            external_order_ids=external_order_ids,
            markets=markets,
            cancel_all=cancel_all,
        )
        return await send_post_request(
            await self.get_session(),
            url,
            EmptyModel,
            json=request_model.to_api_request_json(exclude_none=True),
            api_key=self._get_api_key(),
        )
