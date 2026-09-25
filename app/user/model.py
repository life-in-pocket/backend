from sqlalchemy import String

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str]