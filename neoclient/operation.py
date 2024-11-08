import functools
import inspect
from dataclasses import dataclass, field
from json import JSONDecodeError
from types import FunctionType, MethodType
from typing import Any, Callable, Generic, MutableSequence, Optional, TypeVar

import httpx
import pydantic
from httpx import Client
from pydantic import BaseModel
from typing_extensions import ParamSpec

from neoclient.di import compose, inject_request, inject_response

from .exceptions import NotAnOperationError
from .middleware import Middleware
from .models import ClientOptions, Request, RequestOpts, Response
from .typing import Dependency

__all__ = (
    "set_operation",
    "has_operation",
    "get_operation",
    "Operation",
)

PS = ParamSpec("PS")
RT_co = TypeVar("RT_co", covariant=True)

ATTRIBUTE_OPERATION: str = "operation"


def set_operation(func: Callable, operation: "Operation", /) -> None:
    setattr(func, ATTRIBUTE_OPERATION, operation)


def has_operation(func: Callable, /) -> bool:
    return hasattr(func, ATTRIBUTE_OPERATION)


def get_operation(func: Callable, /) -> "Operation":
    operation: Optional[Operation] = getattr(func, ATTRIBUTE_OPERATION, None)

    if operation is None:
        raise NotAnOperationError(f"{func!r} is not an operation")

    return operation


@dataclass
class Operation(Generic[PS, RT_co]):
    func: Callable[PS, RT_co]
    client_options: ClientOptions
    request_options: RequestOpts
    client: Optional[Client] = None
    response: Optional[Dependency] = None
    middleware: Middleware = field(default_factory=Middleware)
    request_dependencies: MutableSequence[Dependency] = field(default_factory=list)
    response_dependencies: MutableSequence[Dependency] = field(default_factory=list)

    def __call__(self, *args: PS.args, **kwargs: PS.kwargs) -> Any:
        client: Client

        if self.client is not None:
            client = self.client
        else:
            # Build a disposable client using the available client options
            client = self.client_options.build()

        # Create a clone of the request options, so that mutations don't
        # affect the original copy.
        # Mutations to the request options will occur during composition.
        pre_request: RequestOpts = self.request_options.copy()

        # Compose the request using the provided arguments
        compose(self.func, pre_request, args, kwargs)

        # Compose the request using each of the composition dependencies
        request_dependency: Dependency
        for request_dependency in self.request_dependencies:
            inject_request(request_dependency, pre_request)

        # Validate the pre-request (e.g. to ensure no path params have been missed)
        pre_request.validate()

        request: Request = pre_request.build(client)

        return_annotation: Any = inspect.signature(self.func).return_annotation

        if return_annotation is RequestOpts:
            return pre_request
        if return_annotation is Request:
            return request

        follow_redirects: bool = pre_request.follow_redirects

        @self.middleware.compose
        def send_request(request: Request, /) -> Response:
            httpx_response: httpx.Response = client.send(
                request,
                follow_redirects=follow_redirects,
            )

            return Response.from_httpx_response(httpx_response)

        response: Response = send_request(request)

        # Feed the response through each of the response dependencies
        response_dependency: Dependency
        for response_dependency in self.response_dependencies:
            inject_response(response_dependency, response)

        if self.response is not None:
            resolved_response: Any

            # If the response dependency is a class-style decorator, resolve
            # the response against the class instance's `__call__` method, otherwise
            # inspection of the dependency may inadvertently be inspecting the
            # `__init__` method instead.
            if not isinstance(self.response, (FunctionType, MethodType)) and hasattr(
                self.response, "__call__"
            ):
                resolved_response = inject_response(self.response.__call__, response)
            else:
                resolved_response = inject_response(self.response, response)

            if return_annotation is inspect.Parameter.empty:
                return resolved_response
            else:
                return pydantic.parse_obj_as(return_annotation, resolved_response)

        if return_annotation is inspect.Parameter.empty:
            try:
                return response.json()
            except JSONDecodeError:
                return response.text
        if return_annotation is None:
            return None
        if return_annotation is Response:
            return response
        if isinstance(return_annotation, type) and issubclass(
            return_annotation, BaseModel
        ):
            return return_annotation.parse_obj(response.json())

        return pydantic.parse_raw_as(return_annotation, response.text)

    @property
    def wrapper(self) -> Callable[PS, RT_co]:
        @functools.wraps(self.func)
        def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> RT_co:
            if inspect.ismethod(self.func):
                # Read off `self` or `cls`
                _, *args = args  # type: ignore

            return self(*args, **kwargs)

        set_operation(wrapper, self)

        return wrapper
