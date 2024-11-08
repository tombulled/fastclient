import dataclasses
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    MutableSequence,
    Optional,
    Sequence,
    TypeVar,
)

import httpx
from httpx import URL, BaseTransport, Cookies, Headers, Limits, QueryParams, Timeout
from httpx._auth import Auth
from mediate.protocols import MiddlewareCallable
from roster import Record
from typing_extensions import ParamSpec

from neoclient.di import get_parameters, validate_fields

from . import converters
from .constants import USER_AGENT
from .defaults import (
    DEFAULT_AUTH,
    DEFAULT_BASE_URL,
    DEFAULT_COOKIES,
    DEFAULT_ENCODING,
    DEFAULT_EVENT_HOOKS,
    DEFAULT_FOLLOW_REDIRECTS,
    DEFAULT_HEADERS,
    DEFAULT_LIMITS,
    DEFAULT_MAX_REDIRECTS,
    DEFAULT_PARAMS,
    DEFAULT_TIMEOUT,
    DEFAULT_TRUST_ENV,
)
from .enums import HTTPHeader, HTTPMethod
from .middleware import Middleware
from .models import ClientOptions, Request, RequestOpts, Response
from .operation import Operation, get_operation
from .types import (
    AuthTypes,
    CertTypes,
    CookiesTypes,
    DefaultEncodingTypes,
    EventHooks,
    HeadersTypes,
    ProxiesTypes,
    QueryParamsTypes,
    TimeoutTypes,
    URLTypes,
    VerifyTypes,
)
from .typing import Dependency

__all__ = (
    "Session",
    "Client",
    "NeoClient",
)


T = TypeVar("T")

PS = ParamSpec("PS")
RT = TypeVar("RT")

D = TypeVar("D", bound=Dependency)


class BaseService:
    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


@dataclass(init=False)
class Session(httpx.Client):
    auth: Optional[Auth]
    params: QueryParams
    headers: Headers
    cookies: Cookies
    timeout: Timeout
    follow_redirects: bool
    max_redirects: int
    event_hooks: Dict[str, List[Callable]]
    base_url: URL
    trust_env: bool

    def __init__(
        self,
        base_url: URLTypes = DEFAULT_BASE_URL,
        *,
        auth: Optional[AuthTypes] = DEFAULT_AUTH,
        params: Optional[QueryParamsTypes] = DEFAULT_PARAMS,
        headers: Optional[HeadersTypes] = DEFAULT_HEADERS,
        cookies: Optional[CookiesTypes] = DEFAULT_COOKIES,
        verify: VerifyTypes = True,
        cert: Optional[CertTypes] = None,
        http1: bool = True,
        http2: bool = False,
        proxies: Optional[ProxiesTypes] = None,
        mounts: Optional[Mapping[str, BaseTransport]] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        follow_redirects: bool = DEFAULT_FOLLOW_REDIRECTS,
        limits: Limits = DEFAULT_LIMITS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        event_hooks: Optional[EventHooks] = DEFAULT_EVENT_HOOKS,
        transport: Optional[BaseTransport] = None,
        app: Optional[Callable[..., Any]] = None,
        trust_env: bool = DEFAULT_TRUST_ENV,
        default_encoding: DefaultEncodingTypes = DEFAULT_ENCODING,
    ) -> None:
        params = (
            converters.convert_query_params(params)
            if params is not None
            else QueryParams()
        )
        headers = (
            converters.convert_headers(headers) if headers is not None else Headers()
        )
        cookies = (
            converters.convert_cookies(cookies) if cookies is not None else Cookies()
        )
        timeout = (
            converters.convert_timeout(timeout) if timeout is not None else Timeout()
        )
        base_url = URL(base_url)

        # Set a default User-Agent header
        headers.setdefault(HTTPHeader.USER_AGENT, USER_AGENT)

        super().__init__(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            proxies=proxies,
            mounts=mounts,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks,
            transport=transport,
            app=app,
            base_url=base_url,
            trust_env=trust_env,
            default_encoding=default_encoding,
        )


@dataclass(init=False)
class Client:
    client: Optional[httpx.Client]
    middleware: Middleware
    default_response: Optional[Dependency] = None
    request_dependencies: MutableSequence[Dependency] = field(default_factory=list)
    response_dependencies: MutableSequence[Dependency] = field(default_factory=list)

    def __init__(
        self,
        client: Optional[httpx.Client] = None,
        middleware: Optional[Middleware] = None,
        default_response: Optional[Dependency] = None,
        request_dependencies: Optional[Sequence[Dependency]] = None,
        response_dependencies: Optional[Sequence[Dependency]] = None,
    ) -> None:
        self.client = client
        self.middleware = middleware if middleware is not None else Middleware()
        self.default_response = default_response
        self.request_dependencies = (
            [*request_dependencies] if request_dependencies is not None else []
        )
        self.response_dependencies = (
            [*response_dependencies] if response_dependencies is not None else []
        )

    def bind(self, func: Callable[PS, RT], /) -> Callable[PS, RT]:
        operation: Operation = get_operation(func)

        # Create a clone of the operation's middleware, so that when the client's
        # middleware gets added, it doesn't mutate the original
        middleware: Middleware = Middleware()
        middleware.add_all(operation.middleware.record)

        # Create a clone of the operation's request dependencies, so that when
        # the client's request dependencies get added, it doesn't mutate the original
        request_dependencies: MutableSequence[Dependency] = []
        request_dependencies.extend(operation.request_dependencies)

        # Create a clone of the operation's response dependencies, so that when
        # the client's response dependencies get added, it doesn't mutate the original
        response_dependencies: MutableSequence[Dependency] = []
        response_dependencies.extend(operation.response_dependencies)

        bound_operation: Operation[PS, RT] = dataclasses.replace(
            operation,
            client=self.client,
            middleware=middleware,
            request_dependencies=request_dependencies,
            response_dependencies=response_dependencies,
        )

        # If the operation doesn't have a response, use the client's default response
        # if one is available
        if bound_operation.response is None and self.default_response is not None:
            bound_operation.response = self.default_response

        # Add the client's middleware
        bound_operation.middleware.add_all(self.middleware.record)

        # Add the client's request dependencies
        request_dependencies.extend(self.request_dependencies)

        # Add the client's response dependencies
        response_dependencies.extend(self.response_dependencies)

        return bound_operation.wrapper

    def request(
        self,
        method: str,
        endpoint: str,
        /,
        *,
        response: Optional[Dependency] = None,
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        client_options: ClientOptions = ClientOptions()
        pre_request: RequestOpts = RequestOpts(
            method=method,
            url=endpoint,
        )

        operation_response: Optional[Callable] = None

        if response is not None:
            operation_response = response
        elif self.default_response is not None:
            operation_response = self.default_response

        def decorator(func: Callable[PS, RT], /) -> Callable[PS, RT]:
            # Create a copy of the client's middleware
            middleware: Middleware = Middleware()
            middleware.add_all(self.middleware.record)

            # Create a copy of the client's request dependencies
            request_dependencies: MutableSequence[Dependency] = []
            request_dependencies.extend(self.request_dependencies)

            # Create a copy of the client's response dependencies
            response_dependencies: MutableSequence[Dependency] = []
            response_dependencies.extend(self.response_dependencies)

            operation: Operation[PS, RT] = Operation(
                func=func,
                client_options=client_options,
                request_options=pre_request,
                client=self.client,
                middleware=middleware,
                response=operation_response,
                request_dependencies=request_dependencies,
                response_dependencies=response_dependencies,
            )

            # Validate operation function parameters are acceptable
            validate_fields(get_parameters(func, operation.request_options))

            return operation.wrapper

        return decorator

    def put(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.PUT.name, endpoint, response=response)

    def get(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.GET.name, endpoint, response=response)

    def post(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.POST.name, endpoint, response=response)

    def head(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.HEAD.name, endpoint, response=response)

    def patch(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.PATCH.name, endpoint, response=response)

    def delete(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.DELETE.name, endpoint, response=response)

    def options(
        self, endpoint: str, /, *, response: Optional[Dependency] = None
    ) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]:
        return self.request(HTTPMethod.OPTIONS.name, endpoint, response=response)

    def request_depends(self, dependency: D, /) -> D:
        self.request_dependencies.append(dependency)

        return dependency

    def response_depends(self, dependency: D, /) -> D:
        self.response_dependencies.append(dependency)

        return dependency


class NeoClient(Client):
    def __init__(
        self,
        base_url: URLTypes = DEFAULT_BASE_URL,
        *,
        auth: Optional[AuthTypes] = DEFAULT_AUTH,
        params: Optional[QueryParamsTypes] = DEFAULT_PARAMS,
        headers: Optional[HeadersTypes] = DEFAULT_HEADERS,
        cookies: Optional[CookiesTypes] = DEFAULT_COOKIES,
        verify: VerifyTypes = True,
        cert: Optional[CertTypes] = None,
        http1: bool = True,
        http2: bool = False,
        proxies: Optional[ProxiesTypes] = None,
        mounts: Optional[Mapping[str, BaseTransport]] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        follow_redirects: bool = DEFAULT_FOLLOW_REDIRECTS,
        limits: Limits = DEFAULT_LIMITS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        event_hooks: Optional[EventHooks] = DEFAULT_EVENT_HOOKS,
        transport: Optional[BaseTransport] = None,
        app: Optional[Callable[..., Any]] = None,
        trust_env: bool = DEFAULT_TRUST_ENV,
        default_encoding: DefaultEncodingTypes = DEFAULT_ENCODING,
        middleware: Optional[Sequence[MiddlewareCallable[Request, Response]]] = None,
        default_response: Optional[Dependency] = None,
        request_dependencies: Optional[Sequence[Dependency]] = None,
        response_dependencies: Optional[Sequence[Dependency]] = None,
    ) -> None:
        super().__init__(
            client=Session(
                auth=auth,
                params=params,
                headers=headers,
                cookies=cookies,
                verify=verify,
                cert=cert,
                http1=http1,
                http2=http2,
                proxies=proxies,
                mounts=mounts,
                timeout=timeout,
                follow_redirects=follow_redirects,
                limits=limits,
                max_redirects=max_redirects,
                event_hooks=event_hooks,
                transport=transport,
                app=app,
                base_url=base_url,
                trust_env=trust_env,
                default_encoding=default_encoding,
            ),
            middleware=(
                Middleware(record=Record(middleware))
                if middleware is not None
                else Middleware()
            ),
            default_response=default_response,
            request_dependencies=(
                request_dependencies if request_dependencies is not None else []
            ),
            response_dependencies=(
                response_dependencies if response_dependencies is not None else []
            ),
        )
