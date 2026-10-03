import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User

# In-memory test SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_password_hashing():
    raw_pw = "secretPass123"
    hashed = hash_password(raw_pw)
    assert hashed != raw_pw
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("wrongPass", hashed) is False


def test_jwt_token_flow():
    payload = {"sub": "123", "username": "testuser"}
    token = create_access_token(payload)
    assert token is not None
    decoded = decode_access_token(token)
    assert decoded["sub"] == "123"
    assert decoded["username"] == "testuser"


def test_user_registration_and_login(client, db_session):
    # Register new user
    res = client.post("/register", data={
        "full_name": "Test User",
        "email": "test@pocketsmart.ai",
        "username": "testuser",
        "password": "mypassword123",
        "confirm_password": "mypassword123"
    }, follow_redirects=False)

    assert res.status_code == 302
    assert res.headers["location"] == "/dashboard"
    assert "access_token" in res.cookies

    # Test duplicate registration
    res_dup = client.post("/register", data={
        "full_name": "Test User 2",
        "email": "test@pocketsmart.ai",
        "username": "testuser2",
        "password": "mypassword123",
        "confirm_password": "mypassword123"
    })
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.text

    # Test login success
    res_login = client.post("/login", data={
        "login": "test@pocketsmart.ai",
        "password": "mypassword123"
    }, follow_redirects=False)
    assert res_login.status_code == 302
    assert res_login.headers["location"] == "/dashboard"

    # Test login invalid password
    res_bad = client.post("/login", data={
        "login": "test@pocketsmart.ai",
        "password": "wrongpassword"
    })
    assert res_bad.status_code == 401
    assert "Invalid email/username or password" in res_bad.text


def test_api_token_endpoint(client, db_session):
    # Seed user
    user = User(
        full_name="API User",
        email="api@pocketsmart.ai",
        username="apiuser",
        hashed_password=hash_password("apipassword123")
    )
    db_session.add(user)
    db_session.commit()

    # Call /token
    res = client.post("/token", json={
        "login": "apiuser",
        "password": "apipassword123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "api@pocketsmart.ai"
