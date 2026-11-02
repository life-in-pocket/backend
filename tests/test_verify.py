import pytest
from sqlalchemy import select

from app.user.model import User
from app.user.service import hash_token

EMAIL = "user@example.com"
REGISTER_PAYLOAD = {"username": "user", "email": EMAIL, "password": "secret123"}


async def _register_with_token(client, db, token: str) -> User:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    user = await db.scalar(select(User).where(User.email == EMAIL))
    user.verification_token_hash = hash_token(token)
    await db.commit()
    return user

@pytest.mark.asyncio
async def test_verify_with_token(client):
    user = await _register_with_token(client, db, "test-token")
    response = await client.post("/auth/verify", json={"token": "test-token"})
    assert response.status_code == 200

    await db.refresh(user)
    assert user.email_verified == True
    assert user.verification_token_hash is None

@pytest.mark.asyncio
async def test_verify_token_is_single_use(client, db):
    await _register_with_token(client, db, "t")

    await client.post("/auth/verify", json={"token": "t"})
    response = await client.post("/auth/verify", json={"token": "t"})
    assert response.status_code == 400