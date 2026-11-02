from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.user.model import User
from app.user.service import hash_token

EMAIL = "b@example.com"
PAYLOAD = {"username": "bohdan", "email": EMAIL, "password": "secret123"}


async def _register_with_token(client, db, token: str) -> User:
    await client.post("/auth/register", json=PAYLOAD)
    user = await db.scalar(select(User).where(User.email == EMAIL))
    user.verification_token_hash = hash_token(token)
    user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()
    return user


async def test_verify_with_valid_token(client, db):
    user = await _register_with_token(client, db, "test-token")

    response = await client.post("/auth/verify", json={"token": "test-token"})
    assert response.status_code == 200

    await db.refresh(user)
    assert user.email_verified is True
    assert user.verification_token_hash is None


async def test_verify_token_is_single_use(client, db):
    await _register_with_token(client, db, "t")

    await client.post("/auth/verify", json={"token": "t"})
    response = await client.post("/auth/verify", json={"token": "t"})
    assert response.status_code == 400


async def test_verify_unknown_token_returns_400(client, db):
    response = await client.post("/auth/verify", json={"token": "nope"})
    assert response.status_code == 400