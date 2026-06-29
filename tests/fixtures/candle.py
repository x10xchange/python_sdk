from decimal import Decimal
from typing import List

from x10.models.candle import CandleModel
from x10.models.http import WrappedStreamResponseModel
from x10.models.stream_rpc import StreamRpcResponseModel


def create_candle_stream_message():
    return WrappedStreamResponseModel[List[CandleModel]](
        data=[
            CandleModel(
                open=Decimal("3458.64"),
                low=Decimal("3399.07"),
                high=Decimal("3476.89"),
                close=Decimal("3414.85"),
                volume=Decimal("3.938"),
                timestamp=1721106000000,
            )
        ],
        ts=1721283121979,
        seq=1,
    )


def create_candle_stream_rpc_message():
    return StreamRpcResponseModel(
        type="CANDLE",
        data=[
            CandleModel(
                open=Decimal("3458.64"),
                low=Decimal("3399.07"),
                high=Decimal("3476.89"),
                close=Decimal("3414.85"),
                volume=Decimal("3.938"),
                timestamp=1721106000000,
            )
        ],
        ts=1721283121979,
        seq=1,
        subscription="candles.last.BTC-USD.PT1M",
    )
