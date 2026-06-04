from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: str
    user_quota_override: Optional[int] = None
    overage_user_price_override: Optional[Decimal] = None
    status: Literal["active", "paused", "cancelled"] = "active"
    start_date: date
    end_date: Optional[date] = None
    next_billing_date: date


class SubscriptionOut(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    price: Decimal
    user_quota_override: Optional[int] = None
    overage_user_price_override: Optional[Decimal] = None
    status: str
    start_date: date
    end_date: Optional[date] = None
    next_billing_date: date
    is_billable: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionStatusUpdate(BaseModel):
    status: Literal["active", "paused", "cancelled"]
