from typing import Any, Callable, Mapping, Tuple

from di import SolvedDependent
from di.api.providers import DependencyProviderType
from pydantic import BaseModel, Required

from neoclient import api
from neoclient.di.impl import _build_bind_hook, _execute, _solve, get_parameters, validate_fields, request_container
from neoclient.params import Parameter

from ..models import RequestOpts


def compose(
    func: Callable,
    request: RequestOpts,
    # TODO: Use *args and **kwargs instead?
    args: Tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> None:
    arguments: Mapping[str, Any] = api.bind_arguments(func, args, kwargs)
    fields: Mapping[str, Tuple[Any, Parameter]] = get_parameters(func, request)

    # TODO: Do we still need/want to do this?
    # Validate that the fields are acceptable
    validate_fields(fields)

    model: BaseModel = api.create_model(func.__name__, fields, arguments)

    # By this stage the arguments have been validated
    validated_arguments: Mapping[str, Any] = model.dict()

    field_name: str
    parameter: Parameter
    for field_name, (_, parameter) in fields.items():
        argument: Any = validated_arguments[field_name]

        # If no argument was provided, and a value is not required for this
        # parameter, skip composition.
        if argument is None and parameter.default is not Required:
            continue

        dependent: DependencyProviderType[None] = parameter.get_composition_dependent(
            argument
        )

        with request_container.bind(_build_bind_hook(request)):
            solved: SolvedDependent[None] = _solve(
                request_container,
                dependent,
                # TODO: Make this configurable?
                use_cache=True,
            )

        _execute(
            request_container,
            solved,
            {
                RequestOpts: request,
            },
        )
