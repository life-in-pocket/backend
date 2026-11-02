import pytest


@pytest.mark.asyncio
async def test_register_creates_unverifed_user(client):
    response = await client.post(
        "/auth/register",
        json={"username": "test", "email": "user@example.com", "password": "test"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert "hashed_password" not in response.json()

@pytest.mark.asyncio
async def test_register_dublicate_user(client):
    payload = {"username": "test", "email": "user@example.com", "password": "test"}
    await client.post("auth/register", json=payload)
    response = await client.post(
        "/auth/register",
        json=payload,
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_blocked_until_verified(client):
    await client.post(
        "/auth/register",
        json={"username": "test", "email": "user@example.com", "password": "test"}
    )
    response = await client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "test"}
    )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"username": "test", "email": "user@example.com", "password": "test"}
    )
    response = await client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrong"}
    )

    assert response.status_code == 401
