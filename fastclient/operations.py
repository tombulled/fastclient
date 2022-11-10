import inspect
from dataclasses import dataclass
from json import JSONDecodeError
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

import httpx
import pydantic
from httpx import Client, Response
from pydantic import BaseModel
from typing_extensions import ParamSpec

from .composition.api import compose
from .models import OperationSpecification, RequestOptions
from .resolution.api import resolve

PS = ParamSpec("PS")
RT = TypeVar("RT", covariant=True)


@runtime_checkable
class CallableWithOperation(Protocol[PS, RT]):
    operation: "Operation"

    def __call__(self, *args: PS.args, **kwargs: PS.kwargs) -> RT:
        ...


@dataclass
class Operation(Generic[PS, RT]):
    func: Callable[PS, RT]
    specification: OperationSpecification
    client: Optional[Client]

    def __call__(self, *args: PS.args, **kwargs: PS.kwargs) -> Any:
        request_options: RequestOptions = self.specification.request.merge(
            RequestOptions(
                method=self.specification.request.method,
                url=self.specification.request.url,
            )
        )

        compose(self.func, request_options, args, kwargs)

        request: httpx.Request = request_options.build_request(self.client)

        return_annotation: Any = inspect.signature(self.func).return_annotation

        if return_annotation is RequestOptions:
            return request_options
        if return_annotation is httpx.Request:
            return request

        client: Client = self.client if self.client is not None else Client()

        response: Response = client.send(request)

        if self.specification.response is not None:
            # TODO: Pass `request_options` as well through the resolution process
            return resolve(self.specification.response, response)

        if return_annotation is inspect.Parameter.empty:
            # TODO: Check "Content-Type" header and decide what to do from that
            # E.g., if "application/json" call .json(), if "text/plain" use .text, etc.
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
