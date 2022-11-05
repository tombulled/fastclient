import pytest

from fastclient import utils


def test_parse_format_string() -> None:
    assert utils.parse_format_string("http://foo.com/") == set()
    assert utils.parse_format_string("http://foo.com/{bar}") == {"bar"}
    assert utils.parse_format_string("http://foo.com/{bar!r}") == {"bar"}
    assert utils.parse_format_string("http://foo.com/{bar}/{bar}") == {"bar"}
    assert utils.parse_format_string("http://foo.com/{bar}/{baz}") == {"bar", "baz"}
    assert utils.parse_format_string("http://foo.com/{bar}/{{baz}}") == {"bar"}

    with pytest.raises(ValueError):
        utils.parse_format_string("http://foo.com/{}")

    with pytest.raises(ValueError):
        utils.parse_format_string("http://foo.com/{0}")

    with pytest.raises(ValueError):
        utils.parse_format_string("http://foo.com/{bar }")


def test_bind_arguments() -> None:
    def foo(x: str, /, y: str = "def_y", *, z: str = "def_z"):
        ...

    assert utils.bind_arguments(foo, ("x",), {}) == {
        "x": "x",
        "y": "def_y",
        "z": "def_z",
    }
    assert utils.bind_arguments(foo, ("x", "y"), {}) == {
        "x": "x",
        "y": "y",
        "z": "def_z",
    }
    assert utils.bind_arguments(foo, ("x",), {"y": "y"}) == {
        "x": "x",
        "y": "y",
        "z": "def_z",
    }
    assert utils.bind_arguments(foo, ("x", "y"), {"z": "z"}) == {
        "x": "x",
        "y": "y",
        "z": "z",
    }
    assert utils.bind_arguments(foo, ("x",), {"y": "y", "z": "z"}) == {
        "x": "x",
        "y": "y",
        "z": "z",
    }


def test_is_primitive() -> None:
    class Foo:
        pass

    assert utils.is_primitive("abc")
    assert utils.is_primitive(123)
    assert utils.is_primitive(123.456)
    assert utils.is_primitive(True)
    assert utils.is_primitive(False)
    assert utils.is_primitive(None)
    assert not utils.is_primitive(Foo)
    assert not utils.is_primitive(Foo())


def test_unpack_arguments() -> None:
    def positional_only(arg: str, /):
        ...

    def positional_or_keyword(arg: str):
        ...

    def keyword_only(*, arg: str):
        ...

    def var_positional(*args: str):
        ...

    def var_keyword(**kwargs: str):
        ...

    def kitchen_sink(a: str, /, b: str, *args: str, c: str, **kwargs: str):
        ...

    assert utils.unpack_arguments(positional_only, {"arg": "foo"}) == (("foo",), {})
    assert utils.unpack_arguments(positional_or_keyword, {"arg": "foo"}) == (
        (),
        {"arg": "foo"},
    )
    assert utils.unpack_arguments(keyword_only, {"arg": "foo"}) == ((), {"arg": "foo"})
    assert utils.unpack_arguments(var_positional, {"args": ("foo", "bar", "baz")}) == (
        ("foo", "bar", "baz"),
        {},
    )
    assert utils.unpack_arguments(
        var_keyword, {"kwargs": {"name": "sam", "age": 43}}
    ) == ((), {"name": "sam", "age": 43})
    assert utils.unpack_arguments(
        kitchen_sink,
        {
            "a": "a",
            "b": "b",
            "args": ("arg1", "arg2"),
            "c": "c",
            "kwargs": {"key1": "val1", "key2": "val2"},
        },
    ) == (
        ("a", "arg1", "arg2"),
        {
            "b": "b",
            "c": "c",
            "key1": "val1",
            "key2": "val2",
        },
    )
