from decimal import Decimal


def create_orderbook_message():
    from x10.perpetual.orderbooks import OrderbookQuantityModel, OrderbookUpdateModel
    from x10.utils.http import WrappedStreamResponse

    return WrappedStreamResponse[OrderbookUpdateModel](
        type="SNAPSHOT",
        data=OrderbookUpdateModel(
            market="BTC-USD",
            bid=[
                OrderbookQuantityModel(qty=Decimal("0.008"), price=Decimal("43547.00")),
                OrderbookQuantityModel(qty=Decimal("0.007000"), price=Decimal("43548.00")),
            ],
            ask=[OrderbookQuantityModel(qty=Decimal("0.008"), price=Decimal("43546.00"))],
        ),
        ts=1704798222748,
        seq=570,
    )
