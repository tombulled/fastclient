import collections
import dataclasses
import functools
import inspect
import typing
from typing import (
    Any,
    Callable,
    Final,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import httpx
from di import Container, SolvedDependent, bind_by_type
from di.api.dependencies import DependentBase
from di.api.executor import SupportsSyncExecutor
from di.api.providers import DependencyProvider, DependencyProviderType
from di.dependent import Dependent
from di.executors import SyncExecutor
from pydantic import BaseModel, Required
from pydantic.fields import FieldInfo, ModelField, Undefined, UndefinedType

from neoclient import api, utils
from neoclient.di.dependencies import DEPENDENCIES
from neoclient.di.inference import _infer_parameter, infer_composition_parameter
from neoclient.exceptions import DuplicateParameters, PreparationError, ResolutionError
from neoclient.params import BodyParameter, Parameter, PathParameter, QueryParameter
from neoclient.validation import ValidatedFunction

from ..models import RequestOpts, Response
from .enums import Profile

# FIXME: Refers to `test_client.test_multiple_body_params`
# NeoClient needs to change its behaviour around body parameters based on how many of them there are.
# This logic is currently broken in the new di implementation.
# This could be implemented as some sort of pre-processing?
# After inference happens, a parameter type is known for all function parameters, e.g:
#   [QueryParameter, BodyParameter, BodyParameter, HeaderParameter]
# Each parameter currently gets "prepared" (e.g. it needs to learn about their parameter/model field)
#   Parameters could be "prepared" using more info such as the entire function?
#   e.g. my_parameter.prepare(model_field, model)
#   which is essentially: my_parameter.prepare(parameter, function)
#   need to make sure that inference etc. doesn't need to happen multiple times
#   though if something wants to interrogate the model/function
# This logic is essentially to cover:
# https://fastapi.tiangolo.com/tutorial/body-multiple-params/#multiple-body-parameters
# total_body_fields: int = sum(
#     isinstance(parameter, BodyParameter) for _, parameter in fields.values()
# )
# if total_body_fields > 1:
#     field: str
#     annotation: Any
#     param: Parameter
#     for field, (annotation, param) in fields.items():
#         if not isinstance(param, BodyParameter):
#             continue

#         param = dataclasses.replace(param, embed=True)

#         fields[field] = (annotation, param)

T = TypeVar("T")

EXECUTOR: Final[SupportsSyncExecutor] = SyncExecutor()

DO_NOT_AUTOWIRE: Set[type] = {RequestOpts, Response, httpx.Response}


def validate_fields(fields: Mapping[str, Tuple[Any, Parameter]], /) -> None:
    parameter_aliases: MutableSequence[str] = [
        parameter.alias
        for _, parameter in fields.values()
        if parameter.alias is not None
    ]

    # Validate that there are no parameters using the same alias
    #   For example, the following function should fail validation:
    #       @get("/")
    #       def foo(a: str = Query(alias="name"), b: str = Query(alias="name")): ...
    alias_counts: Mapping[str, int] = collections.Counter(parameter_aliases)
    duplicate_aliases: Set[str] = {
        alias for alias, count in alias_counts.items() if count > 1
    }
    if duplicate_aliases:
        raise DuplicateParameters(f"Duplicate parameters: {duplicate_aliases!r}")


@dataclasses.dataclass(unsafe_hash=True)
class DependencyParameter(Parameter):
    dependency: Optional[Callable] = None
    use_cache: bool = True

    def resolve_request(self, request: RequestOpts, /) -> Any:
        if self.dependency is None:
            raise ResolutionError(
                f"Cannot resolve parameter {type(self)!r} without a dependency"
            )

        return inject_request(self.dependency, request, use_cache=self.use_cache)

    def resolve_response(self, response: Response, /) -> Any:
        if self.dependency is None:
            raise ResolutionError(
                f"Cannot resolve parameter {type(self)!r} without a dependency"
            )

        return inject_response(self.dependency, response, use_cache=self.use_cache)

    def prepare(self, field: ModelField, /) -> None:
        super().prepare(field)

        if self.dependency is not None:
            return

        # NOTE: The annotation will nearly always be callable (e.g. `int`)
        # This check needs to be changed to check for non primitive callables,
        # and more generally, nothing out of the standard library.
        if not callable(field.annotation):
            raise PreparationError(
                f"Failed to prepare parameter: {self!r}. Dependency has non-callable annotation"
            )

        self.dependency = field.annotation

    def get_resolution_dependent(self) -> DependencyProviderType[Any]:
        if self.dependency is None:
            raise NotImplementedError  # TODO: Handle correctly.

        return self.dependency


def _wrap_dependent(
    dependent: DependencyProviderType[T], parameter: inspect.Parameter
) -> DependencyProviderType[T]:
    type_ = (
        Undefined
        if parameter.annotation is inspect.Parameter.empty
        else parameter.annotation
    )

    @functools.wraps(dependent)
    def wrapper(*args, **kwargs) -> T:
        obj: Any = dependent(*args, **kwargs)

        model_field: ModelField = utils.parameter_to_model_field(parameter)
        field_info: FieldInfo = model_field.field_info

        # If there is no resolution (e.g. missing header/query param etc.)
        # and the parameter has a default, then we can omit the value from
        # the arguments.
        # This is done so that Pydantic will use the default value, rather
        # than complaining that None was used.
        if obj is None and utils.has_default(field_info):
            obj = utils.get_default(field_info)

        # No type annotation provided, so can't use pydantic to validate.
        if type_ is Undefined:
            return obj

        return utils.parse_obj_as(type_, obj)

    return wrapper


def _build_bind_hook(subject: Union[RequestOpts, Response], /):
    def _bind_hook(
        param: Optional[inspect.Parameter], dependent: DependentBase[Any]
    ) -> Optional[DependentBase[Any]]:
        # If there's no parameter, then a dependent is already known.
        # As a dependent is already known, we don't need to anything.
        if param is None:
            return None

        # The parameter needs to be stubbed, as a value will be provided
        # during execution.
        if param.annotation in DO_NOT_AUTOWIRE:
            return None  # these should already be stubbed

        parameter: Parameter = _infer_parameter(param, subject)

        return Dependent(_wrap_dependent(parameter.get_resolution_dependent(), param))

    return _bind_hook


def _solve(
    container: Container,
    dependent: DependencyProviderType[T],
    *,
    use_cache: bool = True,
) -> SolvedDependent[T]:
    return container.solve(
        Dependent(dependent, use_cache=use_cache),
        scopes=(None,),
    )


def _execute(
    container: Container,
    solved: SolvedDependent[T],
    values: Mapping[DependencyProvider, Any] | None = None,
) -> T:
    with container.enter_scope(None) as state:
        return solved.execute_sync(
            executor=EXECUTOR,
            state=state,
            values=values,
        )


def _solve_and_execute(
    container: Container,
    dependent: DependencyProviderType[T],
    values: Mapping[DependencyProvider, Any] | None = None,
    *,
    use_cache: bool = True,
) -> T:
    solved: SolvedDependent[T] = _solve(container, dependent, use_cache=use_cache)

    return _execute(container, solved, values)


# TEMP
# composition_container = Container()
request_container = Container()
request_container.bind(bind_by_type(Dependent(RequestOpts, wire=False), RequestOpts))
response_container = Container()
response_container.bind(bind_by_type(Dependent(RequestOpts, wire=False), RequestOpts))
response_container.bind(
    bind_by_type(Dependent(httpx.Response, wire=False), httpx.Response, covariant=True)
)


# inject, solve, execute, resolve, handle
def inject_request(
    dependent: DependencyProviderType[T],
    request: RequestOpts,
    *,
    use_cache: bool = True,
) -> T:
    with request_container.bind(_build_bind_hook(request)):
        solved: SolvedDependent[T] = _solve(
            request_container, dependent, use_cache=use_cache
        )

    return _execute(
        request_container,
        solved,
        {
            RequestOpts: request,
        },
    )


def inject_response(
    dependent: DependencyProviderType[T],
    response: Response,
    *,
    use_cache: bool = True,
) -> T:
    with response_container.bind(_build_bind_hook(response)):
        solved: SolvedDependent[T] = _solve(
            response_container, dependent, use_cache=use_cache
        )

    return _execute(
        response_container,
        solved,
        {
            Response: response,
            # Included as `di` doesn't seem to respect covariance
            httpx.Response: response,
        },
    )


def get_parameters(
    func: Callable, request: RequestOpts
) -> Mapping[str, Tuple[Any, Parameter]]:
    validated_function: ValidatedFunction = ValidatedFunction(func)

    parameters: Mapping[str, inspect.Parameter] = (
        validated_function.signature.parameters
    )

    metas: MutableMapping[str, Tuple[Any, Parameter]] = {}

    parameter: inspect.Parameter
    for parameter in parameters.values():
        annotation: Union[Any, UndefinedType] = (
            parameter.annotation
            if parameter.annotation is not inspect.Parameter.empty
            else Undefined
        )
        meta: Parameter = infer_composition_parameter(parameter, request)

        metas[parameter.name] = (annotation, meta)

    return metas