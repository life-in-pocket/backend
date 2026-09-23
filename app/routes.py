from fastapi import APIRouter, Depends, status, Response, HTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.schema import DayTaskResponse, DayTaskCreate, BlockCreate, DayTaskTimeUpdate, DayTaskDescriptionUpdate
from app.model import Task, DayTask
import datetime


router_task = APIRouter(tags=["Tasks"], prefix="/days")

SessionDep = Annotated[AsyncSession, Depends(get_db)]

@router_task.get("/{date}/tasks", response_model=list[DayTaskResponse], status_code=status.HTTP_200_OK)
async def get_block(date: datetime.date, db: SessionDep):
    stmt = select(DayTask).where(DayTask.date == date).options(joinedload(DayTask.task))
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    logger.info("Data successfully fetched")
    return tasks

@router_task.post("/day-tasks", response_model=DayTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_block(task: BlockCreate, db: SessionDep):
    new_task = Task(
        title=task.title,
        target_default=task.target,
    )
    db.add(new_task)
    await db.flush()

    new_day_task = DayTask(
        task_id=new_task.id,
        date=task.date,
        time=task.time,
        target=task.target,
    )
    db.add(new_day_task)
    await db.commit()

    stmt = (
        select(DayTask, Task.title)
        .where(DayTask.id == new_day_task.id)
        .options(joinedload(DayTask.task))
    )

    result = await db.scalar(stmt)
    logger.info("Data successfully created")
    return result

@router_task.put("/{block_id}", response_model=DayTaskResponse, status_code=status.HTTP_200_OK)
async def change_block(block_id: int, db: SessionDep, block: BlockCreate):
    changed_task = await db.get(DayTask, block_id, options=[joinedload(DayTask.task)])
    changed_task.task.title = block.title
    changed_task.time = block.time
    changed_task.target = block.target
    await db.commit()
    await db.refresh(changed_task)
    logger.info(f"Data with id: {block_id}, successfully updated")
    return changed_task

@router_task.put("/{task_id}/description", response_model=DayTaskResponse, status_code=status.HTTP_200_OK)
async def update_description(task_id: int, db: SessionDep, task: DayTaskDescriptionUpdate):
    update_task = await db.get(DayTask, task_id, options=[joinedload(DayTask.task)])

    if update_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    update_task.description = task.description
    await db.commit()
    await db.refresh(update_task)
    logger.info(f"Description with id: {task_id}, successfully updated")
    return update_task

@router_task.patch("/{task_id}/time", response_model=DayTaskResponse, status_code=status.HTTP_200_OK)
async def update_time(task_id: int, db: SessionDep, task: DayTaskTimeUpdate):
    update_task = await db.get(DayTask, task_id, options=[joinedload(DayTask.task)])
    update_task.time = task.time
    await db.commit()
    await db.refresh(update_task)
    logger.info(f"Time with id: {task_id}, successfully updated")
    return update_task

@router_task.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block(task_id: int, db: SessionDep):
    delete_task = await db.get(Task, task_id)
    await db.delete(delete_task)
    await db.commit()
    logger.info(f"Data with id: {task_id}, successfully deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)