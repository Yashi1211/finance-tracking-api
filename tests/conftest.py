import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client) -> str:
    client.post(
        "/auth/register",
        json={
            "username": "adminuser",
            "password": "secret123",
            "role": "admin",
        },
    )
    r = client.post(
        "/auth/login",
        json={"username": "adminuser", "password": "secret123"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def viewer_token(client) -> str:
    client.post(
        "/auth/register",
        json={
            "username": "viewuser",
            "password": "secret123",
            "role": "viewer",
        },
    )
    r = client.post(
        "/auth/login",
        json={"username": "viewuser", "password": "secret123"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]
