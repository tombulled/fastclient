from typing import List, Protocol, TypeVar, runtime_checkable

from typing_extensions import ParamSpec

from ..models import RequestOptions

__all__: List[str] = [
    "RequestConsumer",
]

T = TypeVar("T", contravariant=True)

PS = ParamSpec("PS")


@runtime_checkable
class RequestConsumer(Protocol):
    def __call__(self, request: RequestOptions, /) -> None:
        ...
