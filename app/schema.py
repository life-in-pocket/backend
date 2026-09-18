from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    time: float
    target: float
    description: str | None = None

class TaskResponse(TaskCreate):
    id: int