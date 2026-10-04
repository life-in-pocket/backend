import datetime
from pydantic import BaseModel
from pydantic import Field, ConfigDict

class DayTaskBase(BaseModel):
    is_active: bool = True
    time: float
    target: float
    description: str | None = None

class DayTaskCreate(DayTaskBase):
    task_id: int
    date: datetime.date = Field(default_factory=datetime.date.today)

class TaskResponse(BaseModel):
    id: int
    title: str
    target_default: float

    model_config = ConfigDict(from_attributes=True)


class DayTaskResponse(BaseModel):
    id: int
    task_id: int
    date: datetime.date
    is_active: bool
    time: float
    target: float
    description: str | None
    task: TaskResponse

    model_config = ConfigDict(from_attributes=True)


class BlockCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    time: float = Field(default=0.0, ge=0.0, le=24)
    target: float = Field(gt=0.0, le=24)
    date: datetime.date = Field(default_factory=datetime.date.today)


class BlockUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    time: float = Field(ge=0.0, le=24)
    target: float = Field(gt=0.0, le=24)


class DayTaskTimeUpdate(BaseModel):
    time: float = Field(ge=0.0, le=24)


class DayTaskDescriptionUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=2000)

class DayRecord(BaseModel):
    date: datetime.date
    time: float

class BlockStatisticResponse(BaseModel):
    title: str
    records: list[DayRecord]