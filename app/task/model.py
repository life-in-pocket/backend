import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Date, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.user.model import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str]
    target_default: Mapped[float] = mapped_column(Float)

    day_tasks: Mapped[list["DayTask"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    owner: Mapped["User"] = relationship(back_populates="tasks")


class DayTask(Base):
    __tablename__ = "day_tasks"
    __table_args__ = (UniqueConstraint("task_id", "date", name="uq_day_tasks_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    date: Mapped[datetime.date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    time: Mapped[float] = mapped_column(Float)
    target: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(nullable=True, default=None)

    task: Mapped["Task"] = relationship(back_populates="day_tasks")

