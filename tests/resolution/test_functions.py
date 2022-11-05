from http import HTTPStatus

from fastclient.enums import HttpMethod
from fastclient.resolution.functions import (
    QueryResolutionFunction,
    HeaderResolutionFunction,
    CookieResolutionFunction,
    QueriesResolutionFunction,
    HeadersResolutionFunction,
    CookiesResolutionFunction,
    BodyResolutionFunction,
    DependencyResolutionFunction,
)
from httpx import Response, Request, QueryParams, Headers, Cookies


def test_QueryResolutionFunction() -> None:
    response_with_param: Response = Response(
        HTTPStatus.OK,
        request=Request(
            HttpMethod.GET,
            "https://foo.com/?name=sam",
            params={"name": "sam"},
        ),
    )
    response_without_param: Response = Response(
        HTTPStatus.OK,
        request=Request(
            HttpMethod.GET,
            "https://foo.com/",
        ),
    )

    assert QueryResolutionFunction("name")(response_with_param) == "sam"
    assert QueryResolutionFunction("name")(response_without_param) is None


def test_HeaderResolutionFunction() -> None:
    response_with_header: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
        headers={"name": "sam"},
    )
    response_without_header: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
    )

    assert HeaderResolutionFunction("name")(response_with_header) == "sam"
    assert HeaderResolutionFunction("name")(response_without_header) is None


def test_CookieResolutionFunction() -> None:
    response_with_cookie: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
        headers={"Set-Cookie": "name=sam; Path=/"},
    )
    response_without_cookie: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
    )

    assert CookieResolutionFunction("name")(response_with_cookie) == "sam"
    assert CookieResolutionFunction("name")(response_without_cookie) is None


def test_QueriesResolutionFunction() -> None:
    response: Response = Response(
        HTTPStatus.OK,
        request=Request(
            HttpMethod.GET,
            "https://foo.com/",
            params={"name": "sam"},
        ),
    )

    assert QueriesResolutionFunction()(response) == QueryParams({"name": "sam"})


def test_HeadersResolutionFunction() -> None:
    response: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
        headers={"name": "sam"},
    )

    assert HeadersResolutionFunction()(response) == Headers({"name": "sam"})


def test_CookiesResolutionFunction() -> None:
    response: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
        headers={"Set-Cookie": "name=sam; Path=/"},
    )

    assert CookiesResolutionFunction()(response) == Cookies({"name": "sam"})


def test_BodyResolutionFunction() -> None:
    response: Response = Response(
        HTTPStatus.OK,
        request=Request(HttpMethod.GET, "https://foo.com/"),
        json={"name": "sam"},
    )

    assert BodyResolutionFunction()(response) == {"name": "sam"}


def test_DependencyResolutionFunction() -> None:
    raise NotImplementedError