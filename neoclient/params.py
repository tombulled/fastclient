from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Generic,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
)

import fastapi.encoders
import httpx
from di.api.providers import DependencyProviderType
from httpx import Cookies, Headers, QueryParams
from pydantic import Required
from pydantic.fields import FieldInfo, ModelField, Undefined

from .consumers import (
    CookieConsumer,
    CookiesConsumer,
    HeaderConsumer,
    HeadersConsumer,
    PathConsumer,
    PathParamsConsumer,
    QueryConsumer,
    QueryParamsConsumer,
    StateConsumer,
)
from .converters import (
    convert_cookie,
    convert_header,
    convert_path_param,
    convert_path_params,
    convert_query_param,
)
from .errors import CompositionError, ResolutionError
from .models import RequestOpts, Response, State
from .resolvers import (
    BodyResolver,
    CookieResolver,
    CookiesResolver,
    HeaderResolver,
    HeadersResolver,
    QueryParamsResolver,
    QueryResolver,
    StateResolver,
)
from .types import CookiesTypes, HeadersTypes, PathParamsTypes, QueryParamsTypes
from .typing import RequestConsumer, RequestResolver, ResponseResolver, Supplier
from .utils import parse_obj_as

__all__ = (
    "QueryParameter",
    "HeaderParameter",
    "CookieParameter",
    "PathParameter",
    "QueryParamsParameter",
    "HeadersParameter",
    "CookiesParameter",
    "PathParamsParameter",
    "BodyParameter",
    "URLParameter",
    "ResponseParameter",
    "RequestParameter",
    "StatusCodeParameter",
    "ReasonParameter",
    "AllRequestStateParameter",
    "AllResponseStateParameter",
    "AllStateParameter",
)

K = TypeVar("K")
V = TypeVar("V")


@dataclass(unsafe_hash=True)
class Parameter(FieldInfo):
    alias: Optional[str] = None
    default: Any = Undefined
    default_factory: Optional[Supplier[Any]] = None
    title: Optional[str] = field(default=None, compare=False)
    description: Optional[str] = field(default=None, compare=False)
    exclude: Union[Set[Union[int, str]], Mapping[Union[int, str], Any], Any] = field(
        default=None, compare=False
    )
    include: Union[Set[Union[int, str]], Mapping[Union[int, str], Any], Any] = field(
        default=None, compare=False
    )
    const: Optional[bool] = field(default=None, compare=False)
    gt: Optional[float] = field(default=None, compare=False)
    ge: Optional[float] = field(default=None, compare=False)
    lt: Optional[float] = field(default=None, compare=False)
    le: Optional[float] = field(default=None, compare=False)
    multiple_of: Optional[float] = field(default=None, compare=False)
    allow_inf_nan: Optional[bool] = field(default=None, compare=False)
    max_digits: Optional[int] = field(default=None, compare=False)
    decimal_places: Optional[int] = field(default=None, compare=False)
    min_items: Optional[int] = field(default=None, compare=False)
    max_items: Optional[int] = field(default=None, compare=False)
    unique_items: Optional[bool] = field(default=None, compare=False)
    min_length: Optional[int] = field(default=None, compare=False)
    max_length: Optional[int] = field(default=None, compare=False)
    allow_mutation: bool = field(default=True, compare=False)
    regex: Optional[str] = field(default=None, compare=False)
    discriminator: Optional[str] = field(default=None, compare=False)
    repr: bool = field(default=True, compare=False)
    extra: Dict[str, Any] = field(default_factory=dict, compare=False)
    alias_priority: Optional[int] = field(
        init=False, repr=False, default=None, compare=False
    )

    def __post_init__(self) -> None:
        # Pydantic validates that the alias is a "strict" string. This means
        # that enums (e.g. `HeaderName`) are unable to be used.
        # To mitigate this, the alias is explicity converted to a string here.
        if self.alias is not None:
            self.alias = str(self.alias)

    # def compose(self, request: RequestOpts, argument: Any, /) -> None:
    #     raise CompositionError(f"Parameter {type(self)!r} is not composable")

    # def resolve_response(self, response: Response, /) -> Any:
    #     raise ResolutionError(
    #         f"Parameter {type(self)!r} is not resolvable for type {Response!r}"
    #     )

    # def resolve_request(self, request: RequestOpts, /) -> Any:
    #     raise ResolutionError(
    #         f"Parameter {type(self)!r} is not resolvable for type {RequestOpts!r}"
    #     )

    def prepare(self, model_field: ModelField, /) -> None:
        if self.alias is None:
            self.alias = model_field.name

    def get_resolution_dependent(self) -> DependencyProviderType[Any]:
        raise ResolutionError(f"Parameter {type(self)!r} is not resolvable")

    def get_composition_dependent(
        self, argument: Any, /
    ) -> DependencyProviderType[None]:
        raise CompositionError(f"Parameter {type(self)!r} is not composable")


class ComposableSingletonParameter(ABC, Parameter, Generic[K, V]):
    def compose(self, request: RequestOpts, argument: Any, /) -> None:
        if self.alias is None:
            raise CompositionError(
                f"Cannot compose parameter {type(self)!r} without an alias"
            )

        # If no argument was provided, and a value is not required for this
        # parameter, skip composition.
        if argument is None and self.default is not Required:
            return

        consumer: RequestConsumer = self.build_consumer(
            self.parse_key(self.alias),
            self.parse_value(argument),
        )

        consumer(request)

    @abstractmethod
    def parse_key(self, key: str, /) -> K: ...

    @abstractmethod
    def parse_value(self, value: Any, /) -> V: ...

    @abstractmethod
    def build_consumer(self, key: K, value: V) -> RequestConsumer: ...


class ResolvableSingletonParameter(ABC, Parameter, Generic[K, V]):
    def resolve_request(self, request: RequestOpts, /) -> V:
        if self.alias is None:
            raise ResolutionError(
                f"Cannot resolve parameter {type(self)!r} without an alias"
            )

        resolver: RequestResolver[V] = self.build_request_resolver(
            self.parse_key(self.alias),
        )

        return resolver(request)

    def resolve_response(self, response: Response, /) -> V:
        if self.alias is None:
            raise ResolutionError(
                f"Cannot resolve parameter {type(self)!r} without an alias"
            )

        resolver: ResponseResolver[V] = self.build_response_resolver(
            self.parse_key(self.alias),
        )

        return resolver(response)

    @abstractmethod
    def parse_key(self, key: str, /) -> K: ...

    @abstractmethod
    def build_request_resolver(self, key: K) -> RequestResolver[V]: ...

    @abstractmethod
    def build_response_resolver(self, key: K) -> ResponseResolver[V]: ...


class ComposableSingletonStringParameter(ComposableSingletonParameter[str, str]):
    def parse_key(self, key: str, /) -> str:
        return key


class ResolvableSingletonStringParameter(
    ResolvableSingletonParameter[str, Optional[str]]
):
    def parse_key(self, key: str, /) -> str:
        return key


class QueryParameter(
    ComposableSingletonParameter[str, Sequence[str]],
    ResolvableSingletonParameter[str, Optional[Sequence[str]]],
):
    def parse_key(self, key: str, /) -> str:
        return key

    def parse_value(self, value: Any, /) -> Sequence[str]:
        return convert_query_param(value)

    def build_consumer(self, key: str, value: Sequence[str]) -> RequestConsumer:
        return QueryConsumer(key, value).consume_request

    def build_request_resolver(
        self, key: str
    ) -> RequestResolver[Optional[Sequence[str]]]:
        return QueryResolver(key).resolve_request

    def build_response_resolver(
        self, key: str
    ) -> ResponseResolver[Optional[Sequence[str]]]:
        return QueryResolver(key).resolve_response

    def get_resolution_dependent(self) -> DependencyProviderType[Optional[str]]:
        if self.alias is None:
            raise Exception  # TODO: Handle properly.

        key: str = self.parse_key(self.alias)

        # WARN: Doesn't currently support Sequence[str]
        # Current thought process on this is that if they care, they should
        # wire-in the parent (e.g. QueryParams in this case).
        def extract_param(params: QueryParams, /) -> Optional[str]:
            return params.get(key)

        return extract_param

    def get_composition_dependent(
        self, argument: Any, /
    ) -> DependencyProviderType[None]:
        def _do_compose(request: RequestOpts, /):
            self.compose(request, argument)

        return _do_compose


@dataclass(unsafe_hash=True)
class HeaderParameter(
    ComposableSingletonParameter[str, Sequence[str]],
    ResolvableSingletonParameter[str, Optional[Sequence[str]]],
):
    convert_underscores: bool = True

    def parse_key(self, key: str, /) -> str:
        if self.convert_underscores:
            return key.replace("_", "-")

        return key

    def parse_value(self, value: Any, /) -> Sequence[str]:
        return convert_header(value)

    def build_consumer(self, key: str, value: Sequence[str]) -> RequestConsumer:
        return HeaderConsumer(key, value).consume_request

    def build_request_resolver(
        self, key: str
    ) -> RequestResolver[Optional[Sequence[str]]]:
        return HeaderResolver(key).resolve_request

    def build_response_resolver(
        self, key: str
    ) -> ResponseResolver[Optional[Sequence[str]]]:
        return HeaderResolver(key).resolve_response


class CookieParameter(
    ComposableSingletonStringParameter, ResolvableSingletonStringParameter
):
    def parse_value(self, value: Any, /) -> str:
        return convert_cookie(value)

    def build_consumer(self, key: str, value: str) -> RequestConsumer:
        return CookieConsumer(key, value).consume_request

    def build_request_resolver(self, key: str) -> RequestResolver[Optional[str]]:
        return CookieResolver(key).resolve_request

    def build_response_resolver(self, key: str) -> ResponseResolver[Optional[str]]:
        return CookieResolver(key).resolve_response


@dataclass(unsafe_hash=True)
class PathParameter(ComposableSingletonStringParameter):
    delimiter: str = "/"

    def parse_value(self, value: Any, /) -> str:
        return convert_path_param(value, delimiter=self.delimiter)

    def build_consumer(self, key: str, value: str) -> RequestConsumer:
        return PathConsumer(key, value).consume_request

    def get_resolution_dependent(self) -> DependencyProviderType[Optional[str]]:
        if self.alias is None:
            raise Exception  # TODO: Handle properly.

        key: str = self.parse_key(self.alias)

        # WARN: Doesn't currently support Sequence[str]
        def extract_param(request: RequestOpts, /) -> Optional[str]:
            return request.path_params.get(key)

        return extract_param


class QueryParamsParameter(Parameter):
    def compose(self, request: RequestOpts, argument: Any, /) -> None:
        params: QueryParamsTypes = parse_obj_as(QueryParamsTypes, argument)  # type: ignore

        QueryParamsConsumer(params).consume_request(request)

    def resolve_request(self, request: RequestOpts, /) -> QueryParams:
        return QueryParamsResolver().resolve_request(request)

    def resolve_response(self, response: Response, /) -> QueryParams:
        return QueryParamsResolver().resolve_response(response)


class HeadersParameter(Parameter):
    def compose(self, request: RequestOpts, argument: Any, /) -> None:
        headers: HeadersTypes = parse_obj_as(HeadersTypes, argument)  # type: ignore

        HeadersConsumer(headers).consume_request(request)

    def resolve_request(self, request: RequestOpts, /) -> Headers:
        return HeadersResolver().resolve_request(request)

    def resolve_response(self, response: Response, /) -> Headers:
        return HeadersResolver().resolve_response(response)


class CookiesParameter(Parameter):
    def compose(self, request: RequestOpts, argument: Any, /) -> None:
        cookies: CookiesTypes = parse_obj_as(CookiesTypes, argument)  # type: ignore

        CookiesConsumer(cookies).consume_request(request)

    def resolve_request(self, request: RequestOpts, /) -> Cookies:
        return CookiesResolver().resolve_request(request)

    def resolve_response(self, response: Response, /) -> Cookies:
        return CookiesResolver().resolve_response(response)


@dataclass(unsafe_hash=True)
class PathParamsParameter(Parameter):
    delimiter: str = "/"

    def compose(self, request: RequestOpts, argument: Any, /) -> None:
        raw_path_params: PathParamsTypes = parse_obj_as(PathParamsTypes, argument)  # type: ignore

        path_params: Mapping[str, str] = convert_path_params(
            raw_path_params, delimiter=self.delimiter
        )

        PathParamsConsumer(path_params).consume_request(request)

    def resolve_request(self, request: RequestOpts) -> MutableMapping[str, str]:
        return request.path_params


@dataclass(unsafe_hash=True)
class BodyParameter(Parameter):
    embed: bool = False

    def compose(self, request: RequestOpts, argument: Any, /) -> None:
        # If the parameter is not required and has no value, it can be omitted
        if argument is None and self.default is not Required:
            return

        json_value: Any = fastapi.encoders.jsonable_encoder(argument)

        if self.embed:
            if self.alias is None:
                raise CompositionError(
                    f"Cannot embed parameter {type(self)!r} without an alias"
                )

            json_value = {self.alias: json_value}

        # If this parameter shouln't be embedded in any pre-existing json,
        # make it the entire JSON request body
        if not self.embed:
            request.json = json_value
        else:
            if request.json is None:
                request.json = json_value
            else:
                request.json.update(json_value)

    def resolve_response(self, response: Response, /) -> Any:
        return BodyResolver()(response)


class URLParameter(Parameter):
    def resolve_request(self, request: RequestOpts, /) -> httpx.URL:
        return request.url

    def resolve_response(self, response: Response, /) -> httpx.URL:
        return response.request.url


class ResponseParameter(Parameter):
    def resolve_response(self, response: Response, /) -> Response:
        return response


class RequestParameter(Parameter):
    def resolve_response(self, response: Response, /) -> httpx.Request:
        return response.request

    def resolve_request(self, request: RequestOpts, /) -> RequestOpts:
        return request


class StatusCodeParameter(Parameter):
    def resolve_response(self, response: Response, /) -> int:
        return response.status_code


class StateParameter(
    ComposableSingletonParameter[str, Any], ResolvableSingletonParameter[str, Any]
):
    def parse_key(self, key: str, /) -> str:
        return key

    def parse_value(self, value: Any, /) -> Any:
        return value

    def build_consumer(self, key: str, value: Any) -> RequestConsumer:
        return StateConsumer(key, value).consume_request

    def build_request_resolver(self, key: str) -> RequestResolver[Any]:
        return StateResolver(key).resolve_request

    def build_response_resolver(self, key: str) -> ResponseResolver[Any]:
        return StateResolver(key).resolve_response


class ReasonParameter(Parameter):
    def resolve_response(self, response: Response, /) -> str:
        return response.reason_phrase


class AllRequestStateParameter(Parameter):
    def resolve_request(self, request: RequestOpts, /) -> State:
        return request.state

    def resolve_response(self, response: Response, /) -> State:
        return response.request.state


class AllResponseStateParameter(Parameter):
    def resolve_response(self, response: Response, /) -> State:
        return response.state


class AllStateParameter(AllResponseStateParameter, AllRequestStateParameter):
    pass
