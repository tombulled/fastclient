# from dataclasses import dataclass
# from typing import Any, Mapping, Optional, Sequence, Union

# from httpx import Headers, QueryParams
# from pydantic import BaseModel

# from neoclient import Depends, Header, Query, State, models
# from neoclient.models import Response
# from neoclient.params import QueryParameter
# from neoclient.resolution import resolve_response

# from . import utils


# def test_resolve_infer_query() -> None:
#     def func(name: str, age: int, is_cool: bool) -> Mapping[str, Union[str, int, bool]]:
#         return {
#             "name": name,
#             "age": age,
#             "is_cool": is_cool,
#         }

#     response: Response = utils.build_response(
#         request=utils.build_request(
#             params={
#                 "name": "sam",
#                 "age": "43",
#                 "is_cool": "true",
#             }
#         )
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == {"name": "sam", "age": 43, "is_cool": True}


# def test_resolve_infer_body() -> None:
#     class SomePydanticModel(BaseModel):
#         name: str
#         age: int

#     @dataclass
#     class SomeDataclass:
#         name: str
#         age: int

#     def func(
#         body_dict: dict, body_pydantic: SomePydanticModel, body_dataclass: SomeDataclass
#     ) -> Mapping[str, Union[dict, SomePydanticModel, SomeDataclass]]:
#         return {
#             "body_dict": body_dict,
#             "body_pydantic": body_pydantic,
#             "body_dataclass": body_dataclass,
#         }

#     response: Response = utils.build_response(
#         json={
#             "name": "sam",
#             "age": 43,
#         },
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == {
#         "body_dict": {
#             "name": "sam",
#             "age": 43,
#         },
#         "body_pydantic": SomePydanticModel(
#             name="sam",
#             age=43,
#         ),
#         "body_dataclass": SomeDataclass(
#             name="sam",
#             age=43,
#         ),
#     }


# def test_resolve_caching() -> None:
#     class Counter:
#         count: int = 0

#     counter: Counter = Counter()

#     class SpyingQuery(QueryParameter):
#         resolution_counter: Counter = counter

#         def resolve_response(self, response: Response, /) -> Optional[Sequence[str]]:
#             self.resolution_counter.count += 1

#             return super().resolve_response(response)

#     query_name_spy: SpyingQuery = SpyingQuery("name")
#     p_query_name_spy: str = query_name_spy  # type: ignore

#     def dependency(
#         name_1: str = p_query_name_spy, name_2: str = p_query_name_spy
#     ) -> Mapping[str, Any]:
#         return {
#             "name_1": name_1,
#             "name_2": name_2,
#         }

#     def func(
#         name_1: str = p_query_name_spy,
#         name_2: str = p_query_name_spy,
#         dependency: Mapping[str, Any] = Depends(dependency),
#     ) -> Mapping[str, Any]:
#         return {
#             "name_1": name_1,
#             "name_2": name_2,
#             "dependency": dependency,
#         }

#     response: Response = utils.build_response(
#         request=utils.build_request(params={"name": "sam"})
#     )

#     assert resolve_response(func, response) == {
#         "name_1": "sam",
#         "name_2": "sam",
#         "dependency": {
#             "name_1": "sam",
#             "name_2": "sam",
#         },
#     }
#     assert query_name_spy.resolution_counter.count == 1


# def test_resolve_default(response: Response) -> None:
#     def func(query: str = Query("query", default="default")) -> str:
#         return query

#     resolved: Any = resolve_response(func, response)

#     assert resolved == "default"


# def test_resolve_state_present() -> None:
#     message: str = "Hello, World!"

#     def func(message: str = State("message")) -> str:
#         return message

#     response: Response = utils.build_response(
#         state=models.State({"message": message}),
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == message


# def test_resolve_state_missing(response: Response) -> None:
#     default_message: str = "Hello, Default!"

#     def func(message: str = State("message", default=default_message)) -> str:
#         return message

#     resolved: Any = resolve_response(func, response)

#     assert resolved == default_message


# def test_resolve_query_single() -> None:
#     def func(name: str = Query()) -> str:
#         return name

#     response: Response = utils.build_response(
#         request=utils.build_request(
#             params=QueryParams((("name", "sam"), ("name", "bob")))
#         )
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == "sam"


# def test_resolve_query_multi() -> None:
#     def func(name: Sequence[str] = Query()) -> Sequence[str]:
#         return name

#     response: Response = utils.build_response(
#         request=utils.build_request(
#             params=QueryParams((("name", "sam"), ("name", "bob")))
#         )
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == ["sam", "bob"]


# def test_resolve_header_single() -> None:
#     def func(name: str = Header()) -> str:
#         return name

#     response: Response = utils.build_response(
#         headers=Headers((("name", "sam"), ("name", "bob")))
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == "sam"


# def test_resolve_header_multi() -> None:
#     def func(name: Sequence[str] = Header()) -> Sequence[str]:
#         return name

#     response: Response = utils.build_response(
#         headers=Headers((("name", "sam"), ("name", "bob")))
#     )

#     resolved: Any = resolve_response(func, response)

#     assert resolved == ["sam", "bob"]
