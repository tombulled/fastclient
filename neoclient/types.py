from http.cookiejar import CookieJar
from typing import Any, Callable, List, Mapping, Sequence, Tuple, TypeVar, Union

import httpx
from httpx import Auth, Cookies, Headers, QueryParams
from httpx._types import (
    AsyncByteStream,
    CertTypes,
    ProxiesTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    ResponseContent,
    ResponseExtensions,
    SyncByteStream,
    TimeoutTypes,
    URLTypes,
    VerifyTypes,
)
from typing_extensions import TypeAlias

__all__ = (
    "AuthTypes",
    "CertTypes",
    "ProxiesTypes",
    "RequestContent",
    "RequestData",
    "RequestExtensions",
    "RequestFiles",
    "ResponseContent",
    "ResponseExtensions",
    "TimeoutTypes",
    "URLTypes",
    "VerifyTypes",
    "Primitive",
    "QueryTypes",
    "HeaderTypes",
    "CookieTypes",
    "PathTypes",
    "QueryParamsTypes",
    "HeadersTypes",
    "CookiesTypes",
    "PathParamsTypes",
    "MethodTypes",
    "JsonTypes",
    "StreamTypes",
    "EventHook",
    "EventHooks",
    "DefaultEncodingTypes",
)

# NOTE: This type is needed as `httpx._types.AuthTypes` uses forward references
# which pydantic struggles to resolve.
AuthTypes = Union[
    Tuple[Union[str, bytes], Union[str, bytes]],
    Callable[[httpx.Request], httpx.Request],
    Auth,
]

StrOrBytes = TypeVar("StrOrBytes", str, bytes)

Primitive: TypeAlias = Union[
    str,
    int,
    float,
    bool,
    None,
]
QueryTypes: TypeAlias = Any
HeaderTypes: TypeAlias = Union[Primitive, Sequence[Primitive]]
CookieTypes: TypeAlias = Any
PathTypes: TypeAlias = Union[Primitive, Sequence[Primitive]]
# NOTE: This `QueryParamsTypes` differs from `httpx._types.QueryParamTypes`
# as it accepts sequences instead of lists/tuples
QueryParamsTypes: TypeAlias = Union[
    QueryParams,
    Mapping[str, Union[Primitive, Sequence[Primitive]]],
    Sequence[Tuple[str, Primitive]],
    Sequence[str],  # added
    str,
    bytes,
]
HeadersTypes: TypeAlias = Union[
    Headers,
    Mapping[StrOrBytes, StrOrBytes],
    Sequence[Tuple[StrOrBytes, StrOrBytes]],
]
CookiesTypes: TypeAlias = Union[
    Cookies,
    CookieJar,
    Mapping[str, str],
    Sequence[Tuple[str, str]],
]
PathParamsTypes: TypeAlias = Union[
    Mapping[str, PathTypes],
    Sequence[Tuple[str, PathTypes]],
]

MethodTypes: TypeAlias = Union[str, bytes]
JsonTypes: TypeAlias = Any
StreamTypes: TypeAlias = Union[SyncByteStream, AsyncByteStream]
EventHook: TypeAlias = Callable[..., Any]
EventHooks: TypeAlias = Mapping[str, List[EventHook]]
DefaultEncodingTypes: TypeAlias = Union[str, Callable[[bytes], str]]
