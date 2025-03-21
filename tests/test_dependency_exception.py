from typing_extensions import Annotated
from fastapi import Depends, FastAPI, HTTPException
from fastapi.dependencies.requesterrors import RequestErrors
from fastapi.param_functions import Query
from fastapi.testclient import TestClient

app = FastAPI()


def dep_test_exception():
    raise HTTPException(status_code=400, detail="Invalid request")


async def dep_test_exception_async():
    raise HTTPException(status_code=400, detail="Invalid request")


@app.get("/users-no-raise", raise_from_deps=False)
def put_user_no_raise(dep: dict = Depends(dep_test_exception)):
    return {"message": "OK", "dep": dep}


@app.get("/users")
def put_user(dep: dict = Depends(dep_test_exception)):
    return {"message": "OK"}


@app.get("/users-no-raise-async", raise_from_deps=False)
async def put_user_async_no_raise(dep: dict = Depends(dep_test_exception_async)):
    return {"message": "OK", "dep": dep}


@app.get("/users-async")
async def put_user_async(dep: dict = Depends(dep_test_exception_async)):
    return {"message": "OK"}


@app.get("/users-no-error")
def get_user_no_error(
    caught_validation_errors: RequestErrors,
    dep: Annotated[int, Query()] = None,
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors}


@app.get("/users-error")
def get_user_error(dep: Annotated[int, Query()]):
    return {"message": "OK"}


@app.get("/users-no-error-async")
async def get_user_no_error_async(
    caught_validation_errors: RequestErrors, dep: Annotated[int, Query()] = None
):
    return {"message": "OK", "dep": dep, "errors": caught_validation_errors.errors}


@app.get("/users-error-async")
async def get_user_error_async(dep: Annotated[int, Query()]):
    return {"message": "OK"}


client = TestClient(app)


def test_raise_no_deps_active_continue_operation():
    response = client.get("/users-no-raise")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "OK", "dep": None}


def test_async_raise_no_deps_active_continue_operation():
    # TODO: Implement configuration to enable this test to pass
    response = client.get("/users-no-raise-async")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "OK", "dep": None}


def test_raise_no_deps_inactive_short_circuits():
    response = client.get("/users")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}


def test_async_raise_no_deps_inactive_short_circuits():
    response = client.get("/users-async")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}

nonsense_value = "dfkjnkldjfn"

def test_requesterrors_continue_operation():
    response = client.get(f"/users-no-error?dep={nonsense_value}")
    assert response.status_code == 200, response.text
    assert response.json() == {
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
    }


def test_async_requesterrors_continue_operation():
    # TODO: Implement configuration to enable this test to pass
    response = client.get(f"/users-no-error-async?dep={nonsense_value}")
    assert response.status_code == 200, response.text
    assert response.json() == {
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
    }


def test_normal_short_circuits():
    response = client.get(f"/users-error?dep={nonsense_value}")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "input": nonsense_value,
                "loc": ["query", "dep"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "type": "int_parsing",
            }
        ]
    }


def test_async_normal_short_circuits():
    response = client.get(f"/users-error-async?dep={nonsense_value}")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "input": nonsense_value,
                "loc": ["query", "dep"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "type": "int_parsing",
            }
        ]
    }
