from dataclasses import dataclass
from typing import Protocol, Sequence, TypeVar

from fastclient.models import RequestOptions

from .operation import CallableWithOperation
from .types import (
    CookiesTypes,
    HeadersTypes,
    JsonTypes,
    PathsTypes,
    QueriesTypes,
    RequestContent,
    RequestData,
    RequestFiles,
    TimeoutTypes,
    QueryTypes,
    HeaderTypes,
    CookieTypes,
    PathTypes,
)
from .composition.consumers import (
    ContentConsumer,
    CookieConsumer,
    CookiesConsumer,
    DataConsumer,
    FilesConsumer,
    HeaderConsumer,
    HeadersConsumer,
    JsonConsumer,
    PathConsumer,
    PathsConsumer,
    QueriesConsumer,
    QueryConsumer,
    TimeoutConsumer,
)
from .typing import RequestConsumer

__all__: Sequence[str] = (
    "query",
    "header",
    "cookie",
    "path",
    "query_params",
    "headers",
    "cookies",
    "path_params",
    "content",
    "data",
    "files",
    "json",
    "timeout",
)

C = TypeVar("C", bound=CallableWithOperation)


class Decorator(Protocol):
    def __call__(self, func: C, /) -> C:
        ...


@dataclass
class CompositionFacilitator(Decorator):
    composer: RequestConsumer

    def __call__(self, func: C, /) -> C:
        request: RequestOptions = func.operation.specification.request

        self.composer(request)

        return func


def query(key: str, value: QueryTypes) -> Decorator:
    return CompositionFacilitator(QueryConsumer(key, value))


def header(key: str, value: HeaderTypes) -> Decorator:
    return CompositionFacilitator(HeaderConsumer(key, value))


def cookie(key: str, value: CookieTypes) -> Decorator:
    return CompositionFacilitator(CookieConsumer(key, value))


def path(key: str, value: PathTypes) -> Decorator:
    return CompositionFacilitator(PathConsumer(key, value))


def query_params(params: QueriesTypes, /) -> Decorator:
    return CompositionFacilitator(QueriesConsumer(params))


def headers(headers: HeadersTypes, /) -> Decorator:
    return CompositionFacilitator(HeadersConsumer(headers))


def cookies(cookies: CookiesTypes, /) -> Decorator:
    return CompositionFacilitator(CookiesConsumer(cookies))


def path_params(path_params: PathsTypes, /) -> Decorator:
    return CompositionFacilitator(PathsConsumer(path_params))


def content(content: RequestContent, /) -> Decorator:
    return CompositionFacilitator(ContentConsumer(content))


def data(data: RequestData, /) -> Decorator:
    return CompositionFacilitator(DataConsumer(data))


def files(files: RequestFiles, /) -> Decorator:
    return CompositionFacilitator(FilesConsumer(files))


def json(json: JsonTypes, /) -> Decorator:
    return CompositionFacilitator(JsonConsumer(json))


def timeout(timeout: TimeoutTypes, /) -> Decorator:
    return CompositionFacilitator(TimeoutConsumer(timeout))