from fastapi import Depends, FastAPI, HTTPException
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


client = TestClient(app)


def test_dependency_exception_continue_operation():
    response = client.get("/users-no-raise")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "OK", "dep": None}


def test_async_dependency_exception_continue_operation():
    # TODO: Implement configuration to enable this test to pass
    response = client.get("/users-no-raise-async")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "OK", "dep": None}


def test_dependency_exception_short_circuits():
    response = client.get("/users")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}


def test_async_dependency_exception_short_circuits():
    response = client.get("/users-async")
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid request"}
