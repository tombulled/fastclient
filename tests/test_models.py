import pytest

from retrofit.params import Query
from retrofit.enums import ParamType
from sentinel import Missing


def test_field_no_default() -> None:
    param: Query[int] = Query("foo")

    assert param.type == ParamType.QUERY
    assert param.name == "foo"
    assert not param.has_default()

    with pytest.raises(Exception):
        param.default


def test_field_default_static() -> None:
    param: Query[int] = Query("foo", default=123)

    assert param.type == ParamType.QUERY
    assert param.name == "foo"
    assert param.default == 123
    assert param.has_default()