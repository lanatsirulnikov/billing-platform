from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    price: Decimal
    user_quota: int
    overage_user_price: Decimal
    interval: str


class PlanOut(BaseModel):
    id: str
    name: str
    price: Decimal
    user_quota: int
    overage_user_price: Decimal
    interval: str
    created_at: datetime

    class Config:
        from_attributes = True
