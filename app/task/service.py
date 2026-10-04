from collections import defaultdict
import datetime

from fastapi import HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import contains_eager
from typing import Annotated

from app.dependencies import SessionDep, CurrentUser
from app.task.model import DayTask, Task


async def get_owned_day_task(day_task_id: int, db: SessionDep, user: CurrentUser):
    stmt = (
        select(DayTask)
        .join(DayTask.task)
        .where(DayTask.id == day_task_id, Task.owner_id == user.id)
        .options(contains_eager(DayTask.task))
    )

    day_task = await db.scalar(stmt)
    if day_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return day_task

async def statistic_query(first_date: datetime.date, last_date: datetime.date, db: SessionDep, user: CurrentUser):
    stmt = (
        select(DayTask.id, Task.title, DayTask.date, DayTask.time)
        .join(DayTask.task)
        .where(Task.owner_id == user.id)
        .where(DayTask.date >= first_date, DayTask.date <= last_date)
        .order_by(Task.title, DayTask.date)
    )

    result = await db.execute(stmt)
    rows = result.all()

    grouped = defaultdict(list)
    for row in rows:
        grouped[row.title].append({
            "date": row.date,
            "time": row.time,
        })

    return [
        {"title": title, "records": records}
        for title, records in grouped.items()
    ]


OwnedDayTask = Annotated[DayTask, Depends(get_owned_day_task)]
