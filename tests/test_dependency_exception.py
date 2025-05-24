from typing import Annotated, Mapping, Sequence

import pydantic
from fastapi import Depends, FastAPI, HTTPException
from fastapi.dependencies.requesterrors import RequestErrors
from fastapi.param_functions import Query
from fastapi.testclient import TestClient

app = FastAPI()


def isSubsetOf(dict_a: dict, dict_b: dict) -> bool:
    """If dict_a is a subset of dict_b"""
    if isinstance(dict_a, Mapping) and isinstance(dict_b, Mapping):
        keys_a = set(dict_a.keys())
        keys_b = set(dict_b.keys())
        assert keys_a.issubset(keys_b)
        for k, v in dict_a.items():
            b_val = dict_b.get(k)
            assert isSubsetOf(v, b_val)
        return True
    elif (
        not isinstance(dict_a, str)
        and not isinstance(dict_b, str)
        and isinstance(dict_a, Sequence)
        and isinstance(dict_b, Sequence)
    ):
        assert len(dict_a) == len(dict_b)
        for a_val, b_val in zip(dict_a, dict_b):
            assert isSubsetOf(a_val, b_val)
        return True
    assert (dict_a is None and dict_b is None) or dict_a == dict_b
    return True


def dep_test_exception():
    raise HTTPException(status_code=400, detail="Invalid request")


class DepModel(pydantic.BaseModel):
    test_field: int = pydantic.Field(gt=5)


def dep_test_validationerror():
    model = DepModel(test_field=1)
    return model


async def dep_test_exception_async():
    raise HTTPException(status_code=400, detail="Invalid request")


# @app.get("/users-no-raise", raise_from_deps=False)
# def put_user_no_raise(dep: dict = Depends(dep_test_exception)):
#     return {"message": "OK", "dep": dep}


@app.get("/users")
def put_user(dep: dict = Depends(dep_test_exception)):
    return {"message": "OK"}


@app.get("/users-still-raise")
def put_user_raises(
    caught_validation_errors: RequestErrors, dep: dict = Depends(dep_test_exception)
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors()}


@app.get("/users-still-raise-async")
async def put_user_raises_async(
    caught_validation_errors: RequestErrors, dep: dict = Depends(dep_test_exception)
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors()}


# @app.get("/users-no-raise-async", raise_from_deps=False)
# async def put_user_async_no_raise(dep: dict = Depends(dep_test_exception_async)):
#     return {"message": "OK", "dep": dep}


@app.get("/users-async")
async def put_user_async(dep: dict = Depends(dep_test_exception_async)):
    return {"message": "OK"}


@app.get("/users-no-raise-query-param")
def get_user_no_error_query(
    caught_validation_errors: RequestErrors,
    dep: Annotated[int, Query()] = None,
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors()}


@app.get("/users-no-raise-inner-dep")
def get_user_not_raised(
    caught_validation_errors: RequestErrors,
    dep: dict = Depends(dep_test_validationerror),
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors()}


@app.get("/users-no-raise-inner-dep-async")
async def get_user_not_raised_async(
    caught_validation_errors: RequestErrors,
    dep: dict = Depends(dep_test_validationerror),
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors()}


@app.get("/users-error")
def get_user_error(dep: Annotated[int, Query()]):
    return {"message": "OK"}


@app.get("/users-no-error-async")
async def get_user_no_error_async(
    caught_validation_errors: RequestErrors, dep: Annotated[int, Query()] = None
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors()}


@app.get("/users-error-async")
async def get_user_error_async(dep: Annotated[int, Query()]):
    return {"message": "OK"}


client = TestClient(app)


# def test_raise_no_deps_active_continue_operation():
#     response = client.get("/users-no-raise")
#     assert response.status_code == 200, response.text
#     assert response.json() == {"message": "OK", "dep": None}


# def test_async_raise_no_deps_active_continue_operation():
#     # TODO: Implement configuration to enable this test to pass
#     response = client.get("/users-no-raise-async")
#     assert response.status_code == 200, response.text
#     assert response.json() == {"message": "OK", "dep": None}


def test_normal_operation_exception_short_circuits():
    response = client.get("/users")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}


def test_requesterror_exception_short_circuits():
    response = client.get("/users-still-raise")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}


def test_async_equesterror_exception_short_circuits():
    response = client.get("/users-still-raise-async")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}


def test_async_raise_no_deps_inactive_short_circuits():
    response = client.get("/users-async")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}


nonsense_value = "dfkjnkldjfn"


def test_requesterrors_continue_operation():
    response = client.get(f"/users-no-raise-query-param?dep={nonsense_value}")
    assert response.status_code == 200, response.text
    assert isSubsetOf(
        {
            "message": "OK",
            "dep": None,
            "errors": [
                {
                    "input": nonsense_value,
                    "loc": ["query", "dep"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "type": "int_parsing",
                }
            ],
        },
        response.json(),
    )


def test_request_errors_inner_dep_continue_operation():
    response = client.get("/users-no-raise-inner-dep")
    assert response.status_code == 200, response.text
    assert isSubsetOf(
        {
            "message": "OK",
            "dep": None,
            "errors": [
                {
                    "ctx": {"gt": 5},
                    "input": 1,
                    "loc": ["test_field"],
                    "msg": "Input should be greater than 5",
                    "type": "greater_than",
                }
            ],
        },
        response.json(),
    )


def test_async_request_errors_inner_dep_continue_operation():
    response = client.get("/users-no-raise-inner-dep-async")
    assert response.status_code == 200, response.text
    assert isSubsetOf(
        {
            "message": "OK",
            "dep": None,
            "errors": [
                {
                    "ctx": {"gt": 5},
                    "input": 1,
                    "loc": ["test_field"],
                    "msg": "Input should be greater than 5",
                    "type": "greater_than",
                }
            ],
        },
        response.json(),
    )


def test_async_requesterrors_continue_operation():
    # TODO: Implement configuration to enable this test to pass
    response = client.get(f"/users-no-error-async?dep={nonsense_value}")
    assert response.status_code == 200, response.text
    assert isSubsetOf(
        {
            "message": "OK",
            "dep": None,
            "errors": [
                {
                    "input": nonsense_value,
                    "loc": ["query", "dep"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "type": "int_parsing",
                }
            ],
        },
        response.json(),
    )


def test_normal_short_circuits():
    response = client.get(f"/users-error?dep={nonsense_value}")
    assert response.status_code == 422, response.text
    assert isSubsetOf(
        {
            "detail": [
                {
                    "input": nonsense_value,
                    "loc": ["query", "dep"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "type": "int_parsing",
                }
            ]
        },
        response.json(),
    )


def test_async_normal_short_circuits():
    response = client.get(f"/users-error-async?dep={nonsense_value}")
    assert response.status_code == 422, response.text
    assert isSubsetOf(
        {
            "detail": [
                {
                    "input": nonsense_value,
                    "loc": ["query", "dep"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                    "type": "int_parsing",
                }
            ]
        },
        response.json(),
    )
