from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.task.model import Task


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str]

    tasks: Mapped[list["Task"]] = relationship(back_populates="owner", cascade="all, delete-orphan")