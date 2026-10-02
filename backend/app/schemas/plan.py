from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
