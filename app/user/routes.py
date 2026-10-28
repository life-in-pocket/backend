from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.dependencies import SessionDep
from app.user.schema import UserResponse, UserCreate, Token, UserLogin
from app.user.model import User
from app.user.service import create_verification_token, hash_token, send_verification_email, send_welcome_email
from app.core.security import hash_password, verify_password, create_access_token

router_user = APIRouter(prefix="/auth", tags=["Authentication"])

VERIFY_TTL = timedelta(hours=24)

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
    user = await db.scalar(select(User).where(User.email == user_login.email))
    if user is None or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")

@router_user.get("/verify")
async def verify_email(token: str, background: BackgroundTasks, db: SessionDep):
    user = await db.scalar(
        select(User).where(User.verification_token_hash == hash_token(token))
    )
    if user is None or user.verification_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.email_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    await db.commit()

    background.add_task(send_welcome_email, user.email, user.username)
    return {"message": "Email verified"}
