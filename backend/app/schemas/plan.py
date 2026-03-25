from datetime import datetime
from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    price: float
    interval: str
    user_quota: int


class PlanOut(BaseModel):
    id: str
    name: str
    price: float
    interval: str
    user_quota: int
    created_at: datetime

    class Config:
        from_attributes = True
