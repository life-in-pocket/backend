from fastapi import APIRouter, Depends, status
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.database import get_db
from app.schema import TaskResponse
from app.model import Task



router_task = APIRouter(tags=["Tasks"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]

@router_task.get("/", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
async def show_task(db: SessionDep):
    smtm = select(Task)
    tasks = await db.execute(smtm)
    logger.info("Data successfully fetched")
    return tasks
