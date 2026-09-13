from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    time: float
    target: float
    description: str

class TaskResponse(TaskCreate):
    id: int