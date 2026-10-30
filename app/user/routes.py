from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.core.redis import redis_client
from app.dependencies import SessionDep
from app.user.schema import UserResponse, UserCreate, Token, UserLogin, VerifyIn, EmailIn
from app.user.model import User
from app.user.service import create_verification_token, hash_token, send_verification_email, send_welcome_email
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings

router_user = APIRouter(prefix="/auth", tags=["Authentication"])

VERIFY_TTL = timedelta(hours=24)
MAX_LOGIN_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60
LOCK_MAIL_SECONDS = 60

@router_user.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: SessionDep, background_tasks: BackgroundTasks):
    existing_user = await db.scalar(select(User).where(User.email == user.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    token, token_hash = create_verification_token()

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        email_verified=False,
        verification_token_hash=token_hash,
        verification_token_expires_at=datetime.now(timezone.utc) + VERIFY_TTL,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    background_tasks.add_task(send_verification_email, user.email, user.username, token)
    return new_user

@router_user.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: SessionDep):
    attempts_key = f"login_attempts:{user_login.email.lower()}"

    attempts = int(await redis_client.get(attempts_key))
    if attempts >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")

    user = await db.scalar(select(User).where(User.email == user_login.email))
    if user is None or not verify_password(user_login.password, user.hashed_password):
        count = await redis_client.incr(attempts_key)
        if count == 1:
            await redis_client.expire(attempts_key, LOCK_SECONDS)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    await redis_client.delete(attempts_key)

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")

@router_user.post("/verify")
async def verify_email(verify: VerifyIn, background: BackgroundTasks, db: SessionDep):
    user = await db.scalar(
        select(User).where(User.verification_token_hash == hash_token(verify.token))
    )
    if user is None or user.verification_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.email_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    await db.commit()

    if settings.SEND_WELCOME_EMAIL:
        background.add_task(send_welcome_email, user.email, user.username)
    return {"message": "Email verified"}

@router_user.post("/resend-verification", status_code=202)
async def resend_verification(background_tasks: BackgroundTasks, db: SessionDep, adress: EmailIn):
    cooldown_key = f"resend_verification:{adress.email.lower()}"
    if await redis_client.exists(cooldown_key):
        raise HTTPException(status_code=429, detail="Please wait before requesting another email")

    await redis_client.set(cooldown_key, "1", ex=LOCK_MAIL_SECONDS)

    user = await db.scalar(select(User).where(User.email == adress.email))
    if user or not user.verify_email:
        token, token_hash = create_verification_token()
        user.verification_token_hash = token_hash
        user.verification_token_expires_at = datetime.now(timezone.utc) + VERIFY_TTL
        await db.commit()
        background_tasks.add_task(send_verification_email, user.email, user.username, token)

    return {"message": "If the account exists, a new email was sent."}
