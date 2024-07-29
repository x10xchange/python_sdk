from decimal import Decimal


def create_trading_account():
    from x10.perpetual.accounts import StarkPerpetualAccount

    return StarkPerpetualAccount(
        vault=10002,
        # FIXME
        private_key="0x659127796b268530385f753efee81112c628b2bf266e025d3b52d16204c5504",
        public_key="0x0",
        api_key="dummy_api_key",
    )


def create_account_update_trade_message():
    from x10.perpetual.accounts import AccountStreamDataModel
    from x10.perpetual.trades import AccountTradeModel
    from x10.utils.http import WrappedStreamResponse

    return WrappedStreamResponse[AccountStreamDataModel](
        type="TRADE",
        data=AccountStreamDataModel(
            trades=[
                AccountTradeModel(
                    id=1811328331296018432,
                    account_id=3004,
                    market="BTC-USD",
                    order_id=1811328331287359488,
                    side="BUY",
                    price=Decimal("58249.8000000000000000"),
                    qty=Decimal("0.0010000000000000"),
                    value=Decimal("58.2498000000000000"),
                    fee=Decimal("0.0291240000000000"),
                    is_taker=True,
                    trade_type="TRADE",
                    created_time=1720689301691,
                )
            ]
        ),
        ts=1704798222748,
        seq=570,
    )


def create_account_update_unknown_message():
    from x10.perpetual.accounts import AccountStreamDataModel
    from x10.utils.http import WrappedStreamResponse

    return WrappedStreamResponse[AccountStreamDataModel](
        type="UNEXPECTED",
        data=None,
        ts=1704798222748,
        seq=570,
    )
