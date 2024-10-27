from neoclient.models import RequestOpts
from ._common import request_depends
from .api import CS

__all__ = ("persist_pre_request",)


def _persist_pre_request_dependency(request: RequestOpts):
    request.state.pre_request = request


def persist_pre_request(target: CS, /) -> CS:
    return request_depends(_persist_pre_request_dependency)(target)
