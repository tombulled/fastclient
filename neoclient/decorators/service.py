from typing import Any, Callable, Optional, Sequence, Type, TypeVar

from httpx import URL
from mediate.protocols import MiddlewareCallable

from ..models import Request, Response
from ..service import Service
from ..typing import Decorator

__all__: Sequence[str] = ("service",)

S = TypeVar("S", bound=Type[Service])


def service(
    base_url: Optional[str] = None,
    *,
    middleware: Optional[Sequence[MiddlewareCallable[Request, Response]]] = None,
    default_response: Optional[Callable[..., Any]] = None,
) -> Decorator[Type[Service]]:
    def decorate(target: S, /) -> S:
        if base_url is not None:
            target._spec.options.base_url = URL(base_url)
        if middleware is not None:
            target._spec.middleware.add_all(middleware)
        if default_response is not None:
            target._spec.default_response = default_response

        return target

    return decorate