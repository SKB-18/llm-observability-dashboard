"""
Tests for JWT authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_success():
    resp = client.post("/api/v1/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert data["is_active"] is True
    assert "hashed_password" not in data


def test_register_duplicate_username():
    payload = {"username": "bob", "email": "bob@example.com", "password": "secret123"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json={**payload, "email": "bob2@example.com"})
    assert resp.status_code == 409
    assert "username" in resp.json()["detail"].lower()


def test_register_duplicate_email():
    client.post("/api/v1/auth/register", json={"username": "carol", "email": "shared@example.com", "password": "secret123"})
    resp = client.post("/api/v1/auth/register", json={"username": "carol2", "email": "shared@example.com", "password": "secret123"})
    assert resp.status_code == 409
    assert "email" in resp.json()["detail"].lower()


def test_register_short_password():
    resp = client.post("/api/v1/auth/register", json={
        "username": "dave",
        "email": "dave@example.com",
        "password": "short",
    })
    assert resp.status_code == 422


def test_register_invalid_email():
    resp = client.post("/api/v1/auth/register", json={
        "username": "eve",
        "email": "not-an-email",
        "password": "secret123",
    })
    assert resp.status_code == 422


def test_register_short_username():
    resp = client.post("/api/v1/auth/register", json={
        "username": "ab",
        "email": "ab@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _register_and_login(username="user1", password="mypassword"):
    client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
    })
    return client.post("/api/v1/auth/login", data={
        "username": username,
        "password": password,
    })


def test_login_success():
    resp = _register_and_login()
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 10


def test_login_wrong_password():
    client.post("/api/v1/auth/register", json={
        "username": "frank", "email": "frank@example.com", "password": "correctpassword"
    })
    resp = client.post("/api/v1/auth/login", data={"username": "frank", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_unknown_user():
    resp = client.post("/api/v1/auth/login", data={"username": "ghost", "password": "any"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

def test_me_returns_profile():
    login_resp = _register_and_login("grace", "gracepass")
    token = login_resp.json()["access_token"]
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "grace"


def test_me_without_token():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def test_logout():
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert "message" in resp.json()
