# import pytest
# from httpx import Headers
# from pydantic import BaseConfig
# from pydantic.fields import ModelField

# from neoclient import Cookie
# from neoclient.dependence import DependencyParameter, get_fields
# from neoclient.enums import HTTPMethod
# from neoclient.errors import ResolutionError
# from neoclient.models import RequestOpts, Response
# from neoclient.param_functions import Request
# from neoclient.params import (
#     BodyParameter,
#     CookieParameter,
#     HeadersParameter,
#     QueryParameter,
# )

# from .utils import build_response


# def test_get_fields() -> None:
#     def foo(
#         query: str, body: dict, headers: Headers, cookie: int = Cookie()
#     ) -> None: ...

#     assert get_fields(foo) == {
#         "query": (str, QueryParameter(alias="query")),
#         "body": (dict, BodyParameter(alias="body")),
#         "headers": (Headers, HeadersParameter(alias="headers")),
#         "cookie": (int, CookieParameter(alias="cookie")),
#     }


# # def test_DependencyResolver_resolve_response() -> None:
# #     def dependency(response: Response, /) -> Response:
# #         return response

# #     response: Response = build_response()

# #     assert DependencyResolver(dependency).resolve_response(response) == response


# # def test_DependencyResolver_resolve_request() -> None:
# #     def dependency(request=Request()) -> RequestOpts:
# #         return request

# #     request: RequestOpts = RequestOpts(HTTPMethod.GET, "https://foo.com/")

# #     assert DependencyResolver(dependency).resolve_request(request) == request


# def test_DependencyParameter_resolve() -> None:
#     def dependency(response: Response, /) -> Response:
#         return response

#     response: Response = build_response()

#     dependency_parameter_with_dependency: DependencyParameter = DependencyParameter(
#         dependency=dependency
#     )
#     dependency_parameter_without_dependency: DependencyParameter = DependencyParameter(
#         dependency=None
#     )

#     assert dependency_parameter_with_dependency.resolve_response(response) == response

#     with pytest.raises(ResolutionError):
#         dependency_parameter_without_dependency.resolve_response(response)


# def test_DependencyParameter_prepare() -> None:
#     def some_dependency(response: Response, /) -> Response:
#         return response

#     class SomeDependency:
#         response: Response

#         def __init__(self, response: Response) -> None:
#             self.response = response

#     class Config(BaseConfig):
#         arbitrary_types_allowed: bool = True

#     model_field: ModelField = ModelField(
#         name="some_field",
#         type_=SomeDependency,
#         class_validators=None,
#         model_config=Config,
#     )

#     dependency_parameter_with_dependency: DependencyParameter = DependencyParameter(
#         dependency=some_dependency
#     )
#     dependency_parameter_without_dependency: DependencyParameter = DependencyParameter(
#         dependency=None
#     )

#     dependency_parameter_with_dependency.prepare(model_field)

#     assert dependency_parameter_with_dependency.dependency is some_dependency

#     dependency_parameter_without_dependency.prepare(model_field)

#     assert dependency_parameter_without_dependency.dependency == SomeDependency
