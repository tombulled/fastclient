import inspect
from functools import cached_property, wraps
from inspect import Parameter, Signature, signature
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from pydantic.config import Extra
from pydantic.fields import Undefined
from pydantic.main import BaseModel, create_model
from pydantic.typing import get_all_type_hints
from pydantic.utils import to_camel
from typing_extensions import ParamSpec

__all__ = (
    "create_func_model",
    "validate",
    "ValidatedFunction",
)

PS = ParamSpec("PS")
RT = TypeVar("RT")

ConfigType = Union[Type[Any], Mapping[str, Any]]


@overload
def validate(
    func: None = None, *, config: Optional[ConfigType] = None
) -> Callable[[Callable[PS, RT]], Callable[PS, RT]]: ...


@overload
def validate(func: Callable[PS, RT]) -> Callable[PS, RT]: ...


def validate(
    func: Optional[Callable[PS, RT]] = None, *, config: Optional[ConfigType] = None
) -> Union[Callable[PS, RT], Callable[[Callable[PS, RT]], Callable[PS, RT]]]:
    def decorate(func: Callable[PS, RT], /) -> Callable[PS, RT]:
        validated_func: ValidatedFunction[PS, RT] = ValidatedFunction(
            func, config=config
        )

        @wraps(func)
        def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> RT:
            return validated_func.call(*args, **kwargs)

        setattr(wrapper, "validator", validated_func)

        return wrapper

    if func:
        return decorate(func)

    return decorate


def create_func_model(
    name: str,
    fields: Mapping[str, Any],
    *,
    config: Optional[ConfigType] = None,
) -> Type[BaseModel]:
    configurations: Dict[str, Any] = {}

    if isinstance(config, dict):
        configurations.update(config)
    elif isinstance(config, type):
        member_name: str
        member: Any
        for member_name, member in inspect.getmembers(config):
            if member_name.startswith("_"):
                continue

            configurations[member_name] = member

    configurations.setdefault("extra", Extra.forbid)

    Config: Type[Any] = type("Config", (), configurations)

    ValidatedFunctionBaseModel: Type[BaseModel] = type(
        "ValidatedFunctionBaseModel", (BaseModel,), {"Config": Config}
    )

    return create_model(
        to_camel(name),
        __base__=ValidatedFunctionBaseModel,
        **fields,
    )


class ValidatedFunction(Generic[PS, RT]):
    function: Callable[PS, RT]
    model: Type[BaseModel]

    def __init__(
        self, function: Callable[PS, RT], /, *, config: Optional[ConfigType] = None
    ):
        self.function = function

        parameters: Mapping[str, Parameter] = self.signature.parameters
        type_hints: Mapping[str, Any] = get_all_type_hints(function)
        fields: MutableMapping[str, Tuple[Any, Any]] = {}

        parameter_name: str
        parameter: Parameter
        for parameter_name, parameter in parameters.items():
            annotation: Any = (
                Any
                if parameter.annotation is Parameter.empty
                else type_hints[parameter_name]
            )

            default: Any = (
                Undefined if parameter.default is Parameter.empty else parameter.default
            )

            if parameter.kind is Parameter.VAR_POSITIONAL:
                fields[parameter_name] = (Tuple[annotation, ...], None)
            elif parameter.kind is Parameter.VAR_KEYWORD:
                fields[parameter_name] = (Mapping[str, annotation], None)
            else:
                fields[parameter_name] = (annotation, default)

        self.model = create_func_model(function.__name__, fields, config=config)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}(function={self.function!r})>"

    @cached_property
    def signature(self) -> Signature:
        return signature(self.function)

    def bind_arguments(
        self, args: Tuple[Any, ...], kwargs: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return self.signature.bind(*args, **kwargs).arguments

    def prepare_arguments(
        self, arguments: Mapping[str, Any], /
    ) -> Tuple[Tuple[Any, ...], Mapping[str, Any]]:
        args: MutableSequence[Any] = []
        kwargs: MutableMapping[str, Any] = {}

        parameter: Parameter
        for parameter in self.signature.parameters.values():
            argument: Any = arguments[parameter.name]

            if parameter.kind in (
                Parameter.POSITIONAL_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ):
                args.append(argument)
            elif parameter.kind is Parameter.KEYWORD_ONLY:
                kwargs[parameter.name] = argument
            elif parameter.kind is Parameter.VAR_POSITIONAL:
                args.extend(argument)
            elif parameter.kind is Parameter.VAR_KEYWORD:
                kwargs.update(argument)

        return (tuple(args), kwargs)

    def validate_arguments(
        self, args: Tuple[Any, ...], kwargs: Mapping[str, Any]
    ) -> Tuple[Tuple[Any, ...], Mapping[str, Any]]:
        bound_arguments: Mapping[str, Any] = self.bind_arguments(args, kwargs)
        model: BaseModel = self.model(**bound_arguments)
        arguments: Mapping[str, Any] = model.dict()

        return self.prepare_arguments(arguments)

    def call(self, *args: PS.args, **kwargs: PS.kwargs) -> RT:
        validated_args: Tuple[Any, ...]
        validated_kwargs: Mapping[str, Any]
        validated_args, validated_kwargs = self.validate_arguments(args, kwargs)

        return self.function(*validated_args, **validated_kwargs)
