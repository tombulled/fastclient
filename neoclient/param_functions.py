from typing import Any, Callable, Optional, TypeVar

from pydantic.fields import Undefined

from neoclient.di import DependencyParameter

from .params import (
    AllRequestStateParameter,
    AllResponseStateParameter,
    AllStateParameter,
    BodyParameter,
    CookieParameter,
    CookiesParameter,
    HeaderParameter,
    HeadersParameter,
    Parameter,
    PathParameter,
    PathParamsParameter,
    QueryParameter,
    QueryParamsParameter,
    ReasonParameter,
    RequestParameter,
    ResponseParameter,
    StateParameter,
    StatusCodeParameter,
    URLParameter,
)
from .typing import Supplier

__all__ = (
    "Query",
    "Header",
    "Cookie",
    "Path",
    "QueryParams",
    "Headers",
    "Cookies",
    "PathParams",
    "Body",
    "Depends",
    "URL",
    "Reason",
    "Request",
    "Response",
    "StatusCode",
    "State",
    "AllRequestState",
    "AllResponseState",
    "AllState",
)

P = TypeVar("P", bound=Parameter)


def _validate(parameter: P, /) -> P:
    parameter._validate()

    return parameter


def Query(
    name: Optional[str] = None,
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    regex: Optional[str] = None,
) -> QueryParameter:
    return _validate(
        QueryParameter(
            default=default,
            default_factory=default_factory,
            alias=name,
            const=const,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
        )
    )


def Header(
    name: Optional[str] = None,
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    regex: Optional[str] = None,
    convert_underscores: bool = True,
) -> HeaderParameter:
    return _validate(
        HeaderParameter(
            default=default,
            default_factory=default_factory,
            alias=name,
            const=const,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            convert_underscores=convert_underscores,
        )
    )


def Cookie(
    name: Optional[str] = None,
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    regex: Optional[str] = None,
) -> CookieParameter:
    return _validate(
        CookieParameter(
            default=default,
            default_factory=default_factory,
            alias=name,
            const=const,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
        )
    )


def Path(
    name: Optional[str] = None,
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    regex: Optional[str] = None,
    delimiter: str = "/",
) -> PathParameter:
    return _validate(
        PathParameter(
            default=default,
            default_factory=default_factory,
            alias=name,
            const=const,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            delimiter=delimiter,
        )
    )


def QueryParams(
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> QueryParamsParameter:
    return _validate(
        QueryParamsParameter(
            default=default,
            default_factory=default_factory,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
        )
    )


def Headers(
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> HeadersParameter:
    return _validate(
        HeadersParameter(
            default=default,
            default_factory=default_factory,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
        )
    )


def Cookies(
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> CookiesParameter:
    return _validate(
        CookiesParameter(
            default=default,
            default_factory=default_factory,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
        )
    )


def PathParams(
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
    delimiter: str = "/",
) -> PathParamsParameter:
    return _validate(
        PathParamsParameter(
            default=default,
            default_factory=default_factory,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
            delimiter=delimiter,
        )
    )


def Body(
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
    alias: Optional[str] = None,
    embed: bool = False,
) -> BodyParameter:
    return _validate(
        BodyParameter(
            alias=alias,
            default=default,
            default_factory=default_factory,
            embed=embed,
        )
    )


def Depends(
    dependency: Optional[Callable] = None,
    /,
    *,
    use_cache: bool = True,
) -> DependencyParameter:
    return _validate(
        DependencyParameter(
            dependency=dependency,
            use_cache=use_cache,
        )
    )


def URL() -> URLParameter:
    return _validate(URLParameter())


def Request() -> RequestParameter:
    return _validate(RequestParameter())


def Response() -> ResponseParameter:
    return _validate(ResponseParameter())


def StatusCode() -> StatusCodeParameter:
    return _validate(StatusCodeParameter())


def Reason() -> ReasonParameter:
    return _validate(ReasonParameter())


def State(
    name: Optional[str] = None,
    *,
    default: Any = Undefined,
    default_factory: Optional[Supplier[Any]] = None,
) -> StateParameter:
    return _validate(
        StateParameter(
            default=default,
            default_factory=default_factory,
            alias=name,
        )
    )


def AllRequestState() -> AllRequestStateParameter:
    return _validate(AllRequestStateParameter())


def AllResponseState() -> AllResponseStateParameter:
    return _validate(AllResponseStateParameter())


def AllState() -> AllStateParameter:
    return _validate(AllStateParameter())
