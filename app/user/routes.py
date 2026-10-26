from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.responses import JSONResponse

from app.dependencies import get_db
from app.user.schema import UserResponse, UserCreate, Token, UserLogin, EmailSchema
from app.user.model import User
from app.user.service import create_message
from app.core.security import hash_password, verify_password, create_access_token
from app.core.mail import mail

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

@router_user.post("/email")
async def simple_send(email: EmailSchema) -> JSONResponse:
    email = email.adresses

    html = "<p>Hi this test mail, thanks for using Fastapi-mail</p> "

    message = create_message(
        recipients=email,
        subject="Fastapi-mail",
        body=html
    )

    await mail.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})