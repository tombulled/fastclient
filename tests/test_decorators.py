from dataclasses import replace
from io import BytesIO
from typing import Any, Callable, Type

from httpx import URL, Cookies, Headers, QueryParams
from pytest import fixture

from neoclient import converters, decorators, get
from neoclient.auth import Auth, BasicAuth
from neoclient.defaults import DEFAULT_FOLLOW_REDIRECTS
from neoclient.middleware import AuthMiddleware
from neoclient.models import ClientOptions, Request, RequestOpts, Response, State
from neoclient.operation import get_operation
from neoclient.services import Service
from neoclient.types import (
    CookiesTypes,
    HeadersTypes,
    JsonTypes,
    PathParamsTypes,
    QueryParamsTypes,
    RequestContent,
    RequestData,
    RequestFiles,
    TimeoutTypes,
)
from neoclient.typing import CallNext


@fixture
def func() -> Callable[[], RequestOpts]:
    @get("/foo")
    def foo() -> RequestOpts: ...

    return foo


@fixture
def service() -> Type[Service]:
    class SomeService(Service):
        @get("/foo")
        def foo(self): ...

    return SomeService


def test_query(func: Callable) -> None:
    key: str = "name"
    value: str = "sam"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.params = QueryParams({key: value})

    decorators.param(key, value)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_header(func: Callable) -> None:
    key: str = "name"
    value: str = "sam"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.headers = Headers({key: value})

    decorators.header(key, value)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_cookie(func: Callable) -> None:
    key: str = "name"
    value: str = "sam"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.cookies = Cookies({key: value})

    decorators.cookie(key, value)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_path(func: Callable) -> None:
    key: str = "name"
    value: str = "sam"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.path_params = {key: value}

    decorators.path(key, value)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_query_params(func: Callable) -> None:
    query_params: QueryParamsTypes = {"name": "sam"}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.params = converters.convert_query_params(query_params)

    decorators.params(query_params)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_headers(func: Callable) -> None:
    headers: HeadersTypes = {"name": "sam"}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.headers = converters.convert_headers(headers)

    decorators.headers(headers)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_cookies(func: Callable) -> None:
    cookies: CookiesTypes = {"name": "sam"}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.cookies = converters.convert_cookies(cookies)

    decorators.cookies(cookies)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_path_params(func: Callable) -> None:
    path_params: PathParamsTypes = {"name": "sam"}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.path_params = converters.convert_path_params(path_params)

    decorators.path_params(path_params)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_content(func: Callable) -> None:
    content: RequestContent = "content"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.content = content

    decorators.content(content)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_data(func: Callable) -> None:
    data: RequestData = {"name": "sam"}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.data = data

    decorators.data(data)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_files(func: Callable) -> None:
    files: RequestFiles = {"file.txt": BytesIO(b"content")}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.files = files

    decorators.files(files)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_json(func: Callable) -> None:
    json: JsonTypes = {"name": "sam"}

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.json = json

    decorators.json(json)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_timeout(func: Callable) -> None:
    timeout: TimeoutTypes = 5.0

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.timeout = converters.convert_timeout(timeout)

    decorators.timeout(timeout)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_mount(func: Callable) -> None:
    mount: str = "/mount"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.url = URL("/mount/foo")

    decorators.mount(mount)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_base_url(service: Type[Service]) -> None:
    original_client_options: ClientOptions = replace(service._spec.options)

    base_url: str = "https://foo.bar/"

    decorators.base_url(base_url)(service)

    assert service._spec.options == replace(
        original_client_options, base_url=URL(base_url)
    )


def test_middleware(func: Callable) -> None:
    def middleware_foo(call_next: CallNext, request: Request) -> Response:
        return call_next(request)

    def middleware_bar(call_next: CallNext, request: Request) -> Response:
        return call_next(request)

    decorators.middleware(middleware_foo)(func)
    decorators.middleware(middleware_bar)(func)

    assert get_operation(func).middleware.record == [
        middleware_foo,
        middleware_bar,
    ]


def test_request_depends(func: Callable[..., Any]) -> None:
    def dependency_a() -> None:
        pass

    def dependency_b() -> None:
        pass

    decorators.request_depends(dependency_a)(func)
    decorators.request_depends(dependency_b)(func)

    assert get_operation(func).request_dependencies == [
        dependency_a,
        dependency_b,
    ]


def test_response_depends(func: Callable[..., Any]) -> None:
    def dependency_a() -> None:
        pass

    def dependency_b() -> None:
        pass

    decorators.response_depends(dependency_a)(func)
    decorators.response_depends(dependency_b)(func)

    assert get_operation(func).response_dependencies == [
        dependency_a,
        dependency_b,
    ]


def test_user_agent(func: Callable) -> None:
    user_agent: str = "foo/1.0"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.headers = Headers({"User-Agent": user_agent})

    decorators.user_agent(user_agent)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_accept(func: Callable) -> None:
    accept: str = "en-GB"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.headers = Headers({"Accept": accept})

    decorators.accept(accept)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_referer(func: Callable) -> None:
    referer: str = "https://foo.bar/"

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.headers = Headers({"Referer": referer})

    decorators.referer(referer)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_verify_request(func: Callable) -> None:
    client_options: ClientOptions = replace(get_operation(func).client_options)

    verify: bool = False

    decorators.verify(verify)(func)

    assert get_operation(func).client_options == replace(
        client_options,
        verify=verify,
    )


def test_verify_client(service: Type[Service]) -> None:
    original_client_options: ClientOptions = replace(service._spec.options)

    verify: bool = False

    decorators.verify(verify)(service)

    assert service._spec.options == replace(
        original_client_options,
        verify=verify,
    )


def test_persist_pre_request(func: Callable[..., Any]) -> None:
    assert get_operation(func).request_options.state == State()

    decorators.persist_pre_request(func)

    assert len(get_operation(func).request_dependencies) == 1

    pre_request: RequestOpts = func()

    assert hasattr(pre_request.state, "pre_request")
    assert isinstance(pre_request.state.pre_request, RequestOpts)


def test_follow_redirects(func: Callable[..., Any]) -> None:
    follow_redirects: bool = not DEFAULT_FOLLOW_REDIRECTS

    expected_pre_request: RequestOpts = get_operation(func).request_options.copy()
    expected_pre_request.follow_redirects = follow_redirects

    decorators.follow_redirects(follow_redirects)(func)

    assert get_operation(func).request_options == expected_pre_request


def test_auth(func: Callable[..., Any]) -> None:
    auth: Auth = BasicAuth("username", "password")

    decorators.auth(auth)(func)

    assert get_operation(func).middleware.record == [AuthMiddleware(auth)]


def test_basic_auth(func: Callable[..., Any]) -> None:
    username: str = "username"
    password: str = "password"

    decorators.basic_auth(username, password)(func)

    assert get_operation(func).middleware.record == [
        AuthMiddleware(BasicAuth(username, password))
    ]
