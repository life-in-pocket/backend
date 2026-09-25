from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, ForeignKey, Date, Boolean, UniqueConstraint
from app.database import Base
import datetime

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, auto_increment=True)
    title: Mapped[str]
    target_default: Mapped[float] = mapped_column(Float)

    day_tasks: Mapped[list[DayTask]] = relationship(back_populates="task", cascade="all, delete-orphan")

class DayTask(Base):
    __tablename__ = "day_tasks"
    __table_args__ = (
        UniqueConstraint("task_id", "date", name="uq_day_tasks_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, auto_increment=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    date: Mapped[datetime.date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    time: Mapped[float] = mapped_column(Float)
    target: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(nullable=True, default=None)

    task: Mapped[Task] = relationship(Task, back_populates="day_tasks")