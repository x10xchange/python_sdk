from enum import Enum

from hamcrest import assert_that, equal_to, raises

from x10.utils.http import get_url


class _QueryParamEnum(Enum):
    KEY_1 = "VALUE_1"
    KEY_2 = "VALUE_2"


def test_generate_valid_url_from_template():
    assert_that(
        get_url(
            "/info/candles",
            query={
                "param1": "value1",
                "param2": ["value2_1", "value2_2"],
                "param3": None,
                "param4": 0,
                "param5": False,
                "param6": _QueryParamEnum.KEY_1,
                "param7": [_QueryParamEnum.KEY_1, _QueryParamEnum.KEY_2],
            },
        ),
        equal_to(
            "/info/candles?param1=value1&param2=value2_1&param2=value2_2&param4=0&param5=False&param6=VALUE_1&param7=VALUE_1&param7=VALUE_2"  # noqa: E501
        ),
    )
    assert_that(get_url("/info/candles/<market>", market="BTC-USD"), equal_to("/info/candles/BTC-USD"))
    assert_that(
        get_url("/info/candles/<market>/<candle_type>", market="BTC-USD", candle_type="trades"),
        equal_to("/info/candles/BTC-USD/trades"),
    )
    assert_that(lambda: get_url("/info/candles/<market>"), raises(KeyError))
    assert_that(get_url("/info/candles/<market?>"), equal_to("/info/candles"))
    assert_that(get_url("/info/candles/<market?>", market="BTC-USD"), equal_to("/info/candles/BTC-USD"))
    assert_that(get_url("/info/candles/<market?>", market=None), equal_to("/info/candles"))
