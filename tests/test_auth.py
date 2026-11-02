import pytest

PAYLOAD = {"username": "test", "email": "user@example.com", "password": "test"}


async def test_register_creates_unverified_user(client):
    response = await client.post("/auth/register", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == PAYLOAD["email"]
    assert "hashed_password" not in body


async def test_register_duplicate_user(client):
    await client.post("/auth/register", json=PAYLOAD)
    response = await client.post("/auth/register", json=PAYLOAD)
    assert response.status_code == 400


async def test_login_blocked_until_verified(client):
    await client.post("/auth/register", json=PAYLOAD)
    response = await client.post(
        "/auth/login",
        json={"email": PAYLOAD["email"], "password": PAYLOAD["password"]},
    )
    assert response.status_code == 403


async def test_wrong_password(client):
    await client.post("/auth/register", json=PAYLOAD)
    response = await client.post(
        "/auth/login",
        json={"email": PAYLOAD["email"], "password": "wrong"},
    )
    assert response.status_code == 401