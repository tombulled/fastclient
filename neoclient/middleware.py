from dataclasses import dataclass, field
from typing import Optional, Sequence

import mediate
import mediatype
from mediatype import MediaType

from .auth import Auth
from .enums import HTTPHeader
from .exceptions import (
    ExpectedContentTypeError,
    ExpectedHeaderError,
    ExpectedStatusCodeError,
)
from .models import Request, Response
from .typing import CallNext, MiddlewareCallable

__all__ = (
    "Middleware",
    "AuthMiddleware",
    "ExpectedStatusCodeMiddleware",
    "ExpectedHeaderMiddleware",
    "ExpectedContentTypeMiddleware",
    "raise_for_status",
)


class Middleware(mediate.Middleware[Request, Response]):
    pass


@dataclass
class AuthMiddleware(MiddlewareCallable):
    auth: Auth

    def __call__(self, call_next: CallNext, request: Request, /) -> Response:
        return call_next(self.auth.auth(request))


@dataclass(init=False)
class ExpectedStatusCodeMiddleware:
    codes: Sequence[int] = field(default_factory=list)

    def __init__(self, *codes: int) -> None:
        self.codes = codes

    def __call__(self, call_next: CallNext, request: Request, /) -> Response:
        response: Response = call_next(request)

        if response.status_code not in self.codes:
            raise ExpectedStatusCodeError(
                f"Response contained an unexpected status code: {response.status_code}"
            )

        return response


@dataclass
class ExpectedHeaderMiddleware:
    name: str
    value: Optional[str] = None

    def __call__(self, call_next: CallNext, request: Request, /) -> Response:
        response: Response = call_next(request)

        if self.name not in response.headers:
            raise ExpectedHeaderError(name=self.name)

        header_value: str = response.headers[self.name]

        if self.value is not None and header_value != self.value:
            raise ExpectedHeaderError(
                name=self.name, value=header_value, expected_value=self.value
            )

        return response


@dataclass
class ExpectedContentTypeMiddleware:
    content_type: MediaType

    suffix: bool
    parameters: bool

    def __init__(
        self,
        content_type: str,
        /,
        *,
        suffix: Optional[bool] = None,
        parameters: Optional[bool] = None,
    ) -> None:
        self.content_type = mediatype.parse(content_type)

        if suffix is None:
            suffix = self.content_type.suffix is not None
        if parameters is None:
            parameters = self.content_type.parameters is not None

        self.suffix = suffix
        self.parameters = parameters

    def __call__(self, call_next: CallNext, request: Request, /) -> Response:
        response: Response = call_next(request)

        raw_content_type: str = response.headers.get(HTTPHeader.CONTENT_TYPE)

        if raw_content_type is None:
            raise ExpectedHeaderError(HTTPHeader.CONTENT_TYPE)

        content_type: MediaType = mediatype.parse(raw_content_type)

        expected_content_type: str = self._media_type_to_string(self.content_type)
        actual_content_type: str = self._media_type_to_string(content_type)

        if expected_content_type != actual_content_type:
            raise ExpectedContentTypeError(
                expected=expected_content_type, actual=actual_content_type
            )

        return response

    def _media_type_to_string(self, media_type: MediaType, /) -> str:
        return media_type.string(suffix=self.suffix, parameters=self.parameters)


def raise_for_status(call_next: CallNext, request: Request, /) -> Response:
    response: Response = call_next(request)

    response.raise_for_status()

    return response
