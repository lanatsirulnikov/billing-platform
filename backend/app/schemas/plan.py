from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    price: Decimal
    interval: str
    user_quota: int


class PlanOut(BaseModel):
    id: str
    name: str
    price: Decimal
    interval: str
    user_quota: int
    created_at: datetime

    class Config:
        from_attributes = True
