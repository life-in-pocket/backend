from fastapi import APIRouter, Depends, status
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.database import get_db
from app.schema import TaskResponse
from app.model import Task
from app.schema import TaskCreate



router_task = APIRouter(tags=["Tasks"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]

@router_task.get("/", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
async def get_block(db: SessionDep):
    stmt = select(Task)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    logger.info("Data successfully fetched")
    return tasks

@router_task.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_block(task: TaskCreate, db: SessionDep):
    new_task = Task(
        title=task.title,
        time=task.time,
        target=task.target
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    logger.info("Data successfully created")
    return new_task