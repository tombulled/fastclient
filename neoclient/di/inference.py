import collections
import dataclasses
import inspect
import typing
from typing import Any, Mapping, Optional, Set

from di.api.providers import DependencyProviderType
from pydantic import BaseModel
from pydantic.fields import FieldInfo, ModelField

from neoclient import utils
from neoclient.di.dependencies import DEPENDENCIES
from neoclient.params import BodyParameter, Parameter, PathParameter, QueryParameter

from ..models import RequestOpts
from .enums import Profile

__all__ = ("infer_composition_parameter", "infer_resolution_parameter")


def _has_dependency(
    annotation: Any, dependencies: Mapping[type, DependencyProviderType[type]]
) -> Optional[DependencyProviderType[type]]:
    if not inspect.isclass(annotation):
        # If the annotation is not a type, there can't currently be a dependency
        # for it as `di` doesn't support this.
        return None

    dependency: type
    provider: DependencyProviderType[type]
    for dependency, provider in dependencies.items():
        if issubclass(dependency, annotation):
            return provider

    return None


def _is_body_like_annotation(annotation: Any):
    return (
        (
            isinstance(annotation, type)
            and issubclass(annotation, (BaseModel, dict))
        )
        or dataclasses.is_dataclass(annotation)
        or (
            utils.is_generic_alias(annotation)
            and typing.get_origin(annotation) in (collections.abc.Mapping,)
        )
    )


def _infer_parameter(
    parameter: inspect.Parameter,
    *,
    dependencies: Mapping[type, DependencyProviderType[type]],
    path_params: Set[str],
) -> Parameter:
    model_field: ModelField = utils.parameter_to_model_field(parameter)
    field_info: FieldInfo = model_field.field_info

    parameter_meta: Parameter

    # 1. [Explicit] Parameter metadata exists! Let's use that.
    if isinstance(field_info, Parameter):
        parameter_meta = field_info
    # 2. [Path Parameter] Parameter name matches a path parameter, assume a path parameter.
    elif parameter.name in path_params:
        parameter_meta = PathParameter(
            alias=parameter.name,
            default=utils.get_default(field_info),
        )
    # 3. [Dependency] Parameter type is a known dependency
    elif dependency := _has_dependency(parameter.annotation, dependencies):
        raise NotImplementedError  # TEMP! FIXME!
        # return DependencyParameter(dependency=dependency)
    # 4. [Body Parameter] Parameter type indicates a body parameter
    elif _is_body_like_annotation(model_field.annotation):
        parameter_meta = BodyParameter(
            default=utils.get_default(field_info),
        )
    # 5. Otherwise, assume a query parameter
    else:
        parameter_meta = QueryParameter(
            default=utils.get_default(field_info),
        )

    # Create a clone of the parameter so that any mutations do not affect the original
    parameter_clone: Parameter = dataclasses.replace(parameter_meta)

    parameter_clone.prepare(model_field)

    return parameter_clone


def infer_composition_parameter(
    parameter: inspect.Parameter, request_opts: RequestOpts
) -> Parameter:
    path_params: Set[str] = utils.parse_format_string(str(request_opts.url))

    return _infer_parameter(
        parameter, dependencies=DEPENDENCIES[Profile.REQUEST], path_params=path_params
    )


def infer_resolution_parameter(parameter: inspect.Parameter) -> Parameter:
    return _infer_parameter(
        parameter, dependencies=DEPENDENCIES[Profile.RESPONSE], path_params=set()
    )
