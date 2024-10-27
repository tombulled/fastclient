# import pytest

# from neoclient.errors import ResolutionError
# from neoclient.models import RequestOpts, Response, State
# from neoclient.params import (
#     AllRequestStateParameter,
#     AllResponseStateParameter,
#     AllStateParameter,
#     Parameter,
# )

# from . import utils


# def test_AllRequestStateParameter() -> None:
#     state: State = State({"name": "sam", "age": 43})

#     request: RequestOpts = utils.build_pre_request(state=state)
#     response: Response = utils.build_response(request=utils.build_request(state=state))

#     parameter: Parameter = AllRequestStateParameter()

#     assert parameter.resolve_request(request) is state
#     assert parameter.resolve_response(response) is state


# def test_AllResponseStateParameter() -> None:
#     state: State = State({"name": "sam", "age": 43})

#     response: Response = utils.build_response(state=state)

#     parameter: Parameter = AllResponseStateParameter()

#     with pytest.raises(ResolutionError):
#         parameter.resolve_request(utils.build_pre_request())

#     assert parameter.resolve_response(response) is state


# def test_AllStateParameter() -> None:
#     state: State = State({"name": "sam", "age": 43})

#     request: RequestOpts = utils.build_pre_request(state=state)
#     response: Response = utils.build_response(state=state)

#     parameter: Parameter = AllStateParameter()

#     assert parameter.resolve_request(request) is state
#     assert parameter.resolve_response(response) is state
