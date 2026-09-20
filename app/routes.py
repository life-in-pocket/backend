from fastapi import APIRouter, Depends, status, Response
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

@router_task.put("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def change_block(task_id: int, db: SessionDep, task: TaskCreate):
    changed_task = await db.get(Task, task_id)
    changed_task.title = task.title
    changed_task.time = task.time
    changed_task.target = task.target
    await db.commit()
    await db.refresh(changed_task)
    logger.info(f"Data with id: {task_id}, successfully updated")
    return changed_task



@router_task.patch("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_time(task_id: int, db: SessionDep, task: TaskCreate):
    update_task = await db.get(Task, task_id)
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