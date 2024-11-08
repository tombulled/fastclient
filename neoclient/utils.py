import inspect
import string
import typing
from typing import (
    Any,
    Callable,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
)

from httpx import Headers, QueryParams
from pydantic import BaseConfig, BaseModel, create_model
from pydantic.fields import FieldInfo, ModelField, Undefined
from pydantic.typing import display_as_type

__all__ = (
    "parse_format_string",
    "bind_arguments",
    "is_primitive",
    "unpack_arguments",
    "get_default",
    "has_default",
    "parse_obj_as",
    "parameter_to_model_field",
    "is_generic_alias",
)

T = TypeVar("T")


def parse_format_string(format_string: str, /) -> Set[str]:
    """
    Extracts a set of field names from `format_string`

    Example:
        >>> parse_format_string("foo {bar}")
        {"bar"}
    """

    path_params: Set[str] = set()

    field_name: Optional[str]
    for _, field_name, _, _ in string.Formatter().parse(format_string):
        if field_name is None:
            continue

        if not field_name.isidentifier():
            raise ValueError(f"Field name {field_name!r} is not a valid identifier")

        path_params.add(field_name)

    return path_params


def bind_arguments(
    func: Callable, /, args: Tuple[Any, ...], kwargs: Mapping[str, Any]
) -> Mapping[str, Any]:
    bound_arguments: inspect.BoundArguments = inspect.signature(func).bind(
        *args, **kwargs
    )

    bound_arguments.apply_defaults()

    return bound_arguments.arguments


def is_primitive(obj: Any, /) -> bool:
    return isinstance(obj, (str, int, float, bool, type(None)))


def unpack_arguments(
    func: Callable, arguments: Mapping[str, Any]
) -> Tuple[Tuple[Any, ...], Mapping[str, Any]]:
    parameters: Mapping[str, inspect.Parameter] = inspect.signature(func).parameters

    args: MutableSequence[Any] = []
    kwargs: MutableMapping[str, Any] = {}

    parameter: inspect.Parameter
    for parameter in parameters.values():
        if parameter.name not in arguments:
            raise ValueError(f"Missing argument for parameter {parameter.name!r}")

        argument: Any = arguments[parameter.name]

        if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
            args.append(argument)
        elif parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            kwargs[parameter.name] = argument
        elif parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            args.extend(argument)
        else:
            assert parameter.kind == inspect.Parameter.VAR_KEYWORD

            kwargs.update(argument)

    return (tuple(args), kwargs)


def get_default(field_info: FieldInfo, /) -> Any:
    if field_info.default_factory is not None:
        return field_info.default_factory()

    return field_info.default


def has_default(field_info: FieldInfo, /) -> bool:
    return field_info.default is not Undefined or field_info.default_factory is not None


def parse_obj_as(type_: Type[T], obj: Any) -> T:
    parsing_type_name: str = f"ParsingModel[{display_as_type(type_)}]"

    class Config(BaseConfig):
        arbitrary_types_allowed: bool = True

    model_cls: Type[BaseModel] = create_model(
        parsing_type_name,
        __config__=Config,
        __root__=(type_, ...),
    )

    model: BaseModel = model_cls(__root__=obj)

    return getattr(model, "__root__")


def parameter_to_model_field(parameter: inspect.Parameter, /) -> ModelField:
    class Config(BaseConfig):
        arbitrary_types_allowed = True

    annotation: Any = (
        Any if parameter.annotation is inspect.Parameter.empty else parameter.annotation
    )
    default: Any = (
        Undefined if parameter.default is inspect.Parameter.empty else parameter.default
    )

    return ModelField.infer(
        name=parameter.name,
        value=default,
        annotation=annotation,
        class_validators=None,
        config=Config,
    )


def is_generic_alias(type_: Type, /) -> bool:
    return typing.get_origin(type_) is not None


# WARN: Currently unused
def merge_headers(lhs: Headers, rhs: Headers, /, *, overwrite: bool = True) -> Headers:
    if overwrite:
        headers: Headers = lhs.copy()

        key: str
        for key in rhs:
            if key in headers:
                del headers[key]

        return merge_headers(headers, rhs, overwrite=False)
    else:
        # Keep all headers from both
        return Headers((*lhs.multi_items(), *rhs.multi_items()))


# WARN: Currently unused
def merge_query_params(
    lhs: QueryParams, rhs: QueryParams, /, *, overwrite: bool = True
) -> QueryParams:
    if overwrite:
        params: QueryParams = lhs

        key: str
        for key in rhs:
            if key in params:
                params = params.remove(key)

        return merge_query_params(params, rhs, overwrite=False)
    else:
        # Keep all query params from both
        return QueryParams((*lhs.multi_items(), *rhs.multi_items()))


def add_header(headers: Headers, /, key: str, value: str) -> None:
    new_headers: Headers = Headers(((key, value),))

    headers._list.extend(new_headers._list)


def add_headers(lhs: Headers, rhs: Headers, /) -> None:
    """Add all headers from `rhs` to `lhs`, keeping duplicates."""
    key: str
    value: str
    for key, value in rhs.multi_items():
        add_header(lhs, key, value)


def add_params(lhs: QueryParams, rhs: QueryParams, /) -> QueryParams:
    """Return a new QueryParams instance, appending the params from `lhs` and `rhs`"""
    params: QueryParams = lhs

    key: str
    value: str
    for key, value in rhs.multi_items():
        params = params.add(key, value)

    return params
