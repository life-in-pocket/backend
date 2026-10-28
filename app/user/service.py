import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.mail import send_email

logger = logging.getLogger(__name__)

VERIFY_TTL = timedelta(hours=24)


def create_verification_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    print("token:", token)
    print("hash:", hash_token(token))
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verification_expiry() -> datetime:
    return datetime.now(timezone.utc) + VERIFY_TTL


async def send_verification_email(email: str, username: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    try:
        await send_email(
            to=email,
            subject="Verify your email",
            template_name="verify_email.html",
            context={"username": username, "link": link},
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", email)


async def send_welcome_email(email: str, username: str) -> None:
    try:
        await send_email(
            to=email,
            subject="Welcome to Pocket",
            template_name="welcome.html",
            context={"username": username, "frontend_url": settings.FRONTEND_URL},
        )
    except Exception:
        logger.exception("Failed to send welcome email to %s", email)