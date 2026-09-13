from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, auto_increment=True)
    title: Mapped[str]
    time: Mapped[int]
    target: Mapped[int]