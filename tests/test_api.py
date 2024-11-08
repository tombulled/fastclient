import pytest

from neoclient.decorators import get
from neoclient.exceptions import DuplicateParameters
from neoclient.param_functions import Query


def test_get_params_duplicate_explicit():
    with pytest.raises(DuplicateParameters):

        @get("/foo")
        def foo(
            param_1: str = Query("param"), param_2: str = Query("param")
        ) -> None: ...


def test_get_params_duplicate_implicit():
    with pytest.raises(DuplicateParameters):

        @get("/foo")
        def foo(param_1: str, param_2: str = Query("param_1")) -> None: ...
