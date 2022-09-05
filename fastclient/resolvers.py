import dataclasses
import inspect
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Type, Union, Protocol

import param
from param import ParameterSpecification
import pydantic
from httpx import Request, Response
from param import ParameterType
from param.sentinels import Missing, MissingType

from . import utils, api
from .errors import InvalidParameterSpecification
from .enums import ParamType
from .models import RequestOptions
from .parameters import (
    Depends,
    Param,
    Params,
    Path,
    Promise,
    Query,
    Header,
    Cookie,
)


class Resolver(Protocol):
    def __call__(
        self,
        response: Response,
        parameter: param.Parameter,
        *,
        request: Optional[RequestOptions] = None,
    ) -> Any:
        ...


def _get_alias(parameter: param.Parameter, /) -> str:
    return (
        parameter.spec.alias
        if parameter.spec.alias is not None
        else parameter.spec.generate_alias(parameter.name)
    )


def _parse_obj(annotation: Union[MissingType, Any], obj: Any) -> Any:
    if type(obj) is annotation or annotation in (inspect._empty, Missing):
        return obj

    return pydantic.parse_obj_as(annotation, obj)


def resolve_response_param(
    response: Response,
    parameter: param.Parameter,
    *,
    request: Optional[RequestOptions] = None,
) -> Any:
    spec: Param

    if not isinstance(parameter.spec, Param):
        raise Exception("Parameter is not a Param")
    else:
        spec = parameter.spec

    # Enrich parameter specification alias
    spec = dataclasses.replace(parameter.spec, alias=_get_alias(parameter))

    return resolve_param(
        response,
        spec,
        annotation=parameter.annotation,
        request=request,
    )


def resolve_response_params(
    response: Response,
    parameter: param.Parameter,
    *,
    request: Optional[RequestOptions] = None,
) -> Any:
    spec: Params

    if not isinstance(parameter.spec, Params):
        raise Exception("Parameter is not a Params")
    else:
        spec = parameter.spec

    return resolve_multi_param(
        response,
        spec,
        annotation=parameter.annotation,
        request=request,
    )


def resolve_response_depends(
    response: Response,
    parameter: param.Parameter,
    *,
    request: Optional[RequestOptions] = None,
) -> Any:
    spec: Depends

    if not isinstance(parameter.spec, Depends):
        raise Exception("Parameter is not a Depends")
    else:
        spec = parameter.spec

    return resolve_dependency(
        response,
        spec,
        annotation=parameter.annotation,
        request=request,
    )


def resolve_response_promise(
    response: Response,
    parameter: param.Parameter,
    *,
    request: Optional[RequestOptions] = None,
) -> Any:
    spec: Promise

    if not isinstance(parameter.spec, Promise):
        raise Exception("Parameter is not a Promise")
    else:
        spec = parameter.spec

    return resolve_promise(
        response,
        spec,
        annotation=parameter.annotation,
    )


whitelisted_response_resolvers: Dict[type, Resolver] = {
    Param: resolve_response_param,
    Params: resolve_response_params,
    Depends: resolve_response_depends,
    Promise: resolve_response_promise,
}


def resolve(
    response: Response,
    parameter: param.Parameter,
    *,
    request: Optional[RequestOptions] = None,
) -> Any:
    if isinstance(parameter.spec, Param):
        return resolve_response_param(response, parameter, request=request)
    elif isinstance(parameter.spec, Params):
        return resolve_response_params(response, parameter, request=request)
    elif isinstance(parameter.spec, Depends):
        return resolve_response_depends(response, parameter, request=request)
    elif isinstance(parameter.spec, Promise):
        return resolve_response_promise(response, parameter, request=request)
    else:
        raise InvalidParameterSpecification(
            f"Invalid response parameter specification: {parameter.spec!r}"
        )


def resolve_query_param(
    response: Response,
    param: Query,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
) -> Any:
    if param.alias is None:
        raise Exception("Cannot resolve a parameter without an alias")

    if param.alias in response.request.url.params:
        return _parse_obj(annotation, response.request.url.params[param.alias])
    else:
        return param.get_default()


def resolve_header(
    response: Response,
    param: Header,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
) -> Any:
    if param.alias is None:
        raise Exception("Cannot resolve a parameter without an alias")

    if param.alias in response.headers:
        return _parse_obj(annotation, response.headers[param.alias])
    else:
        return param.get_default()


def resolve_cookie(
    response: Response,
    param: Cookie,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
) -> Optional[str]:
    if param.alias is None:
        raise Exception("Cannot resolve a parameter without an alias")

    if param.alias in response.cookies:
        return _parse_obj(annotation, response.cookies[param.alias])
    else:
        return param.get_default()


def resolve_body(
    response: Response, /, *, annotation: Union[Any, MissingType] = Missing
) -> Any:
    # TODO: Massively improve this implementation
    if annotation in (inspect._empty, Missing):
        return response.json()
    else:
        return pydantic.parse_raw_as(annotation, response.text)


def resolve_path_param(
    response: Response,
    param: Path,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
    request: RequestOptions,
) -> str:
    if param.alias is None:
        raise Exception("Cannot resolve a parameter without an alias")

    path_params: Dict[str, Any] = utils.extract_path_params(
        urllib.parse.unquote(str(request.url)),
        urllib.parse.unquote(str(response.request.url)),
    )

    if param.alias in path_params:
        return _parse_obj(annotation, path_params[param.alias])
    else:
        return param.get_default()


def resolve_promise(
    response: Response,
    promise: Promise,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
) -> Union[Request, Response]:
    promised_type: Union[Type[Request], Type[Response]]

    if promise.promised_type is not None:
        promised_type = promise.promised_type
    elif annotation not in (inspect._empty, Missing):
        promised_type = annotation
    else:
        raise Exception("Cannot promise no type!")

    # TODO: Support more promised types?
    if promised_type is Response:
        return response
    elif promised_type is Request:
        return response.request
    else:
        raise Exception(f"Unsupported promised type: {promise.promised_type!r}")


def resolve_multi_param(
    response: Response,
    param: Params,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
    request: Optional[RequestOptions] = None,
) -> Any:
    path_params: Dict[str, Any] = (
        utils.extract_path_params(
            urllib.parse.unquote(str(request.url)),
            urllib.parse.unquote(str(response.request.url)),
        )
        if request is not None
        else {}
    )

    values: Dict[ParamType, Any] = {
        ParamType.QUERY: response.url.params,
        ParamType.HEADER: response.headers,
        ParamType.COOKIE: response.cookies,
        ParamType.PATH: path_params,
    }

    return _parse_obj(annotation, values[param.type])


def resolve_param(
    response: Response,
    param: Param,
    /,
    *,
    annotation: Union[Any, MissingType] = Missing,
    request: Optional[RequestOptions] = None,
) -> Any:
    if param.type is ParamType.QUERY:
        return resolve_query_param(response, param, annotation=annotation)
    elif param.type is ParamType.HEADER:
        return resolve_header(response, param, annotation=annotation)
    elif param.type is ParamType.PATH:
        if request is None:
            raise Exception("Cannot resolve path param if no request provided")

        return resolve_path_param(
            response, param, annotation=annotation, request=request
        )
    elif param.type is ParamType.COOKIE:
        return resolve_cookie(response, param, annotation=annotation)
    elif param.type is ParamType.BODY:
        return resolve_body(response, annotation=annotation)
    else:
        raise Exception(f"Unknown ParamType: {param.type}")


def resolve_dependency(
    response: Response,
    dependency: Depends,
    /,
    *,
    request: Optional[RequestOptions] = None,
    annotation: Union[Any, MissingType] = Missing,
    cached_dependencies: Optional[Dict[Callable[..., Any], Any]] = None,
) -> Any:
    parameter_dependency_callable: Callable

    if dependency.dependency is not None:
        parameter_dependency_callable = dependency.dependency
    elif annotation not in (inspect._empty, Missing):
        if not callable(annotation):
            raise Exception("Dependency has non-callable annotation")

        parameter_dependency_callable = annotation
    else:
        raise Exception("Cannot resolve empty dependency")

    if (
        cached_dependencies is not None
        and dependency.use_cache
        and dependency.dependency in cached_dependencies
    ):
        return cached_dependencies[dependency.dependency]

    parameters: Dict[str, param.Parameter] = api.get_params(
        parameter_dependency_callable, request=request
    )

    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

    if cached_dependencies is None:
        cached_dependencies = {}

    parameter: param.Parameter
    for parameter in parameters.values():
        parameter_spec: ParameterSpecification = parameter.spec

        value: Any

        if isinstance(parameter_spec, Depends):
            value = resolve_dependency(
                response,
                parameter_spec,
                request=request,
                annotation=parameter.annotation,
                cached_dependencies=cached_dependencies,
            )
        else:
            value = resolve(
                response,
                parameter,
                request=request,
            )

        if parameter.type in (
            ParameterType.POSITIONAL_ONLY,
            ParameterType.VAR_POSITIONAL,
        ):
            args.append(value)
        else:
            kwargs[parameter.name] = value

    resolved: Any = parameter_dependency_callable(*args, **kwargs)

    # Cache resolved dependency
    cached_dependencies[parameter_dependency_callable] = resolved

    return resolved
