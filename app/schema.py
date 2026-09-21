import datetime
from pydantic import BaseModel
from pydantic import Field

class TaskCreate(BaseModel):
    title: str
    target_default: float

class TaskResponse(TaskCreate):
    id: int

class BlockCreate(BaseModel):
    title: str
    time: float
    target: float
    
class DayTaskBase(BaseModel):
    is_active: bool = True
    time: float
    target: float
    description: str | None = None

class DayTaskCreate(DayTaskBase):
    task_id: int
    date: datetime.date = Field(default_factory=datetime.date.today)

class DayTaskResponse(DayTaskBase):
    id: int
    task_id: int
    date: datetime.date
    task: TaskResponse