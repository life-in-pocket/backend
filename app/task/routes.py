from fastapi import APIRouter, Depends, status, Response, HTTPException
from typing import Annotated
from sqlalchemy import select
from loguru import logger
from sqlalchemy.orm import contains_eager

from app.dependencies import SessionDep, CurrentUser
from app.task.schema import DayTaskResponse, BlockCreate, DayTaskTimeUpdate, DayTaskDescriptionUpdate, BlockStatisticResponse
from app.task.model import Task, DayTask
from app.task.service import OwnedDayTask, statistic_query
import datetime

from app.user.schema import UserResponse

router_task = APIRouter(tags=["Tasks"], prefix="/days")

@router_task.get("/{date}/tasks", response_model=list[DayTaskResponse])
async def get_block(date: datetime.date, db: SessionDep, current_user: CurrentUser):
    stmt = (
        select(DayTask)
        .join(DayTask.task)
        .where(DayTask.date == date, Task.owner_id == current_user.id)
        .options(contains_eager(DayTask.task))
    )
    result = await db.scalars(stmt)
    return result.all()

@router_task.post("/day-tasks", response_model=DayTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_block(task: BlockCreate, db: SessionDep, user: CurrentUser):
    new_task = Task(
        owner_id=user.id,
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
        select(DayTask)
        .join(DayTask.task)
        .where(DayTask.id == new_day_task.id, Task.owner_id == user.id)
        .options(contains_eager(DayTask.task))
    )

    result = await db.scalar(stmt)
    logger.info("Data successfully created")
    return result

@router_task.put("/{day_task_id}", response_model=DayTaskResponse, status_code=status.HTTP_200_OK)
async def change_block(changed_task: OwnedDayTask, db: SessionDep, block: BlockCreate):
    changed_task.task.title = block.title
    changed_task.time = block.time
    changed_task.target = block.target
    await db.commit()
    logger.info(f"Data with id: {changed_task.id}, successfully updated")
    return changed_task

@router_task.put("/{day_task_id}/description", response_model=DayTaskResponse, status_code=status.HTTP_200_OK)
async def update_description(update_task: OwnedDayTask, db: SessionDep, task: DayTaskDescriptionUpdate):
    update_task.description = task.description
    await db.commit()
    logger.info(f"Description with id: {update_task.id}, successfully updated")
    return update_task

@router_task.patch("/{day_task_id}/time", response_model=DayTaskResponse, status_code=status.HTTP_200_OK)
async def update_time(update_task: OwnedDayTask, db: SessionDep, task: DayTaskTimeUpdate):
    update_task.time = task.time
    await db.commit()
    logger.info(f"Time with id: {update_task.id}, successfully updated")
    return update_task

@router_task.delete("/{day_task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block(delete_task: OwnedDayTask, db: SessionDep):
    await db.delete(delete_task)
    await db.commit()
    logger.info(f"Data with id: {delete_task.id}, successfully deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router_task.get("/username", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(current_user: CurrentUser):
    return current_user

@router_task.get("/statistic", response_model=list[BlockStatisticResponse], status_code=status.HTTP_200_OK)
async def get_statistic(first_date: datetime.date, last_date: datetime.date, db: SessionDep, current_user: CurrentUser):
    statistic_data = await statistic_query(first_date, last_date, db, current_user)
    logger.info(f"Data with successfully fetched")
    return statistic_data