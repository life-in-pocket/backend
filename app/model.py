from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float
from app.database import Base

class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, auto_increment=True)
    title: Mapped[str]
    time: Mapped[float] = mapped_column(Float)
    target: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(nullable=True)