import re
from typing import Optional

from hamcrest import assert_that, equal_to, raises
from pydantic import ValidationError

from x10.utils.model import X10BaseModel


class _TestModel(X10BaseModel):
    market: str
    order_type: Optional[str] = "LIMIT"
    created_time: int
    expiry_time: Optional[int] = None


def test_model_should_parse_json_with_missing_optional_fields():
    model = _TestModel.model_validate_json('{"market": "BTC-USD", "createdTime": 0}')

    assert_that(model, equal_to(_TestModel(market="BTC-USD", created_time=0)))
    assert_that(model.order_type, equal_to("LIMIT"))
    assert_that(model.expiry_time, equal_to(None))


def test_model_should_parse_json():
    model = _TestModel.model_validate_json('{"market": "BTC-USD", "createdTime": 0, "expiryTime": 1}')

    assert_that(model, equal_to(_TestModel(market="BTC-USD", created_time=0, expiry_time=1)))


def test_model_should_throw_error_when_field_is_modified():
    test_model = _TestModel(market="BTC-USD", created_time=0)

    def try_to_modify_field():
        test_model.market = "ETH-USD"

    assert_that(try_to_modify_field, raises(ValidationError, pattern=re.compile("Instance is frozen")))
