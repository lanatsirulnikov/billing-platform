from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: str
    status: Literal["active", "paused", "cancelled"] = "active"
    start_date: date
    end_date: Optional[date] = None
    user_quota_override: Optional[float] = None


class SubscriptionOut(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    status: str
    start_date: date
    end_date: Optional[date] = None
    user_quota_override: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionStatusUpdate(BaseModel):
    status: Literal["active", "paused", "cancelled"]
