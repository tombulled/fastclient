import inspect
from typing import Any, Callable, Mapping, MutableMapping, Optional, TypeVar

import httpx
from di.api.providers import DependencyProviderType
from httpx import Cookies, Headers, QueryParams

from neoclient.models import RequestOpts, State, Response

from .enums import Profile

C = TypeVar("C", bound=Callable[..., Any])

REQUEST_DEPENDENCIES: MutableMapping[type, DependencyProviderType[type]] = {}
RESPONSE_DEPENDENCIES: MutableMapping[type, DependencyProviderType[type]] = {}

DEPENDENCIES: Mapping[Profile, MutableMapping[type, DependencyProviderType[type]]] = {
    Profile.REQUEST: REQUEST_DEPENDENCIES,
    Profile.RESPONSE: RESPONSE_DEPENDENCIES,
}


def dependency(
    func: Optional[Callable] = None, /, *, profile: Optional[Profile] = None
):
    destinations = (
        (DEPENDENCIES[profile],) if profile is not None else DEPENDENCIES.values()
    )

    def decorate(func):
        return_annotation = inspect.signature(func).return_annotation

        for destination in destinations:
            destination[return_annotation] = func

        return func

    if func is None:
        return decorate
    else:
        return decorate(func)


### REQUEST DEPENDENCIES ###


@dependency(profile=Profile.REQUEST)
def request_headers(request: RequestOpts, /) -> Headers:
    return request.headers


@dependency(profile=Profile.REQUEST)
def request_params(request: RequestOpts, /) -> QueryParams:
    return request.params


@dependency(profile=Profile.REQUEST)
def request_cookies(request: RequestOpts, /) -> Cookies:
    return request.cookies


@dependency(profile=Profile.REQUEST)
def request_state(request: RequestOpts, /) -> State:
    return request.state


### RESPONSE DEPENDENCIES


@dependency(profile=Profile.RESPONSE)
def response_headers(response: httpx.Response, /) -> Headers:
    return response.headers


@dependency(profile=Profile.RESPONSE)
def response_cookies(response: httpx.Response, /) -> Cookies:
    return response.cookies


@dependency(profile=Profile.RESPONSE)
def response_request(response: httpx.Response, /) -> httpx.Request:
    return response.request


@dependency(profile=Profile.RESPONSE)
def response_state(response: Response, /) -> State:
    return response.state


@dependency(profile=Profile.RESPONSE)
def response_request_params(request: httpx.Request, /) -> QueryParams:
    return request.url.params
