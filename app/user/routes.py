from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.annotation import Annotated
from sqlalchemy import select

from app.dependencies import get_db
from app.user.schema import UserResponse, UserCreate, UserRegister
from app.core.security import hash_password

router_user = APIRouter(prefix="/")

SessionDep = Annotated[AsyncSession, Depends(get_db)]
@router_user.post("/register",  response_model=UserResponse)
async def register(user: UserCreate, db: SessionDep):
    existing_user = await db.scalar(select(UserCreate).where(UserCreate.email == user.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = UserRegister(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user