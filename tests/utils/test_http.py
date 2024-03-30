from enum import Enum

from hamcrest import assert_that, equal_to, raises

from x10.utils.http import get_url


class _TestEnum(Enum):
    KEY_1 = "VALUE_1"
    KEY_2 = "VALUE_2"


def test_generate_valid_url_from_template():
    assert_that(
        get_url(
            "/foo/bar", query={"q1": "v1", "q2": ["v2", "v3"], "q3": None, "q4": 0, "q5": False, "q6": _TestEnum.KEY_1}
        ),
        equal_to("/foo/bar?q1=v1&q2=v2&q2=v3&q4=0&q5=False&q6=VALUE_1"),
    )
    assert_that(get_url("/foo/<bar>", bar="bar-path"), equal_to("/foo/bar-path"))
    assert_that(lambda: get_url("/foo/<bar>"), raises(KeyError))
    assert_that(get_url("/foo/<bar?>"), equal_to("/foo"))
    assert_that(get_url("/foo/<bar?>", bar="bar-path"), equal_to("/foo/bar-path"))
    assert_that(get_url("/foo/<bar?>", bar=None), equal_to("/foo"))
