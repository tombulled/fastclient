import pytest

from neoclient import Request, Response
from neoclient.auth import Auth, BasicAuth
from neoclient.enums import HTTPHeader
from neoclient.exceptions import ExpectedContentTypeError
from neoclient.middleware import AuthMiddleware, ExpectedContentTypeMiddleware
from neoclient.typing import MiddlewareCallable

from . import utils


def test_ExpectedContentTypeMiddleware_no_suffix_no_parameters() -> None:
    def invoke_middleware(
        middleware: MiddlewareCallable,
        content_type: str,
    ) -> None:
        def call_next(request: Request, /) -> Response:
            return utils.build_response(
                request=request, headers={HTTPHeader.CONTENT_TYPE: content_type}
            )

        middleware(call_next, utils.build_request())

    middleware: MiddlewareCallable = ExpectedContentTypeMiddleware("application/json")

    invoke_middleware(middleware, "application/json")  # ok
    invoke_middleware(middleware, "application/JSON")  # ok
    invoke_middleware(middleware, 'application/json; charset="utf-8"')  # ok
    invoke_middleware(middleware, "application/json+foo")  # ok
    invoke_middleware(middleware, 'application/json+foo; charset="utf-8"')  # ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(middleware, "application/not-json")  # not ok


def test_ExpectedContentTypeMiddleware_suffix_no_parameters() -> None:
    def invoke_middleware(
        middleware: MiddlewareCallable,
        content_type: str,
    ) -> None:
        def call_next(request: Request, /) -> Response:
            return utils.build_response(
                request=request, headers={HTTPHeader.CONTENT_TYPE: content_type}
            )

        middleware(call_next, utils.build_request())

    middleware: MiddlewareCallable = ExpectedContentTypeMiddleware(
        "application/json+opensearch", suffix=True
    )

    invoke_middleware(middleware, "application/json+opensearch")  # ok
    invoke_middleware(middleware, "application/JSON+OpenSearch")  # ok
    invoke_middleware(middleware, 'application/json+opensearch; charset="utf-8"')  # ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(middleware, "application/not-json")  # not ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(middleware, "application/json+not-opensearch")  # not ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(
            middleware, 'application/json+not-opensearch; charset="utf-8"'
        )  # not ok


def test_ExpectedContentTypeMiddleware_suffix_parameters() -> None:
    def invoke_middleware(
        middleware: MiddlewareCallable,
        content_type: str,
    ) -> None:
        def call_next(request: Request, /) -> Response:
            return utils.build_response(
                request=request, headers={HTTPHeader.CONTENT_TYPE: content_type}
            )

        middleware(call_next, utils.build_request())

    middleware: MiddlewareCallable = ExpectedContentTypeMiddleware(
        'application/json+opensearch; charset="utf-8"', suffix=True
    )

    invoke_middleware(middleware, 'application/json+opensearch; charset="utf-8"')  # ok
    invoke_middleware(middleware, 'application/JSON+OpenSearch; CharSet="UTF-8"')  # ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(middleware, "application/not-json")  # not ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(middleware, "application/json+not-opensearch")  # not ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(
            middleware, 'application/json+opensearch; name="bob"'
        )  # not ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(
            middleware, 'application/json+opensearch; charset="utf-9"'
        )  # not ok

    with pytest.raises(ExpectedContentTypeError):
        invoke_middleware(middleware, 'application/json; charset="utf-8"')  # not ok


def test_AuthMiddleware() -> None:
    username: str = "username"
    password: str = "password"
    authorization: str = "Basic dXNlcm5hbWU6cGFzc3dvcmQ="

    def call_next(request: Request, /) -> Response:
        return utils.build_response(request=request)

    middleware: MiddlewareCallable = AuthMiddleware(BasicAuth(username, password))

    request: Request = utils.build_request()

    assert request.headers.get(HTTPHeader.AUTHORIZATION) is None

    middleware(call_next, request)

    assert request.headers.get(HTTPHeader.AUTHORIZATION) == authorization
