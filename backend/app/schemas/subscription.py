from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: str
    status: Literal["active", "paused", "cancelled"] = "active"
    start_date: date
    end_date: Optional[date] = None
    next_billing_date: date
    user_quota_override: Optional[int] = None


class SubscriptionOut(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    price: Decimal
    status: str
    start_date: date
    end_date: Optional[date] = None
    next_billing_date: date
    user_quota_override: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionStatusUpdate(BaseModel):
    status: Literal["active", "paused", "cancelled"]
