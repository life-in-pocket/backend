from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db
from app.user.schema import UserResponse, UserCreate, Token, UserLogin
from app.user.model import User
from app.core.security import hash_password, verify_password, create_access_token

router_user = APIRouter(prefix="/auth", tags=["Authentication"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]

@router_user.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: SessionDep):
    existing_user = await db.scalar(select(User).where(User.email == user.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router_user.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: SessionDep):
    user = await db.scalar(select(User).where(User.email == user_login.email))
    if user is None or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")