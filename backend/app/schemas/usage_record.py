from datetime import datetime, date
from pydantic import BaseModel, Field


class UsageRecordCreate(BaseModel):
    subscription_id: str
    recorded_on: date
    active_user_count: int = Field(..., ge=0)


class UsageRecordOut(BaseModel):
    id: str
    subscription_id: str
    recorded_on: date
    active_user_count: int = Field(..., ge=0)
    created_at: datetime

    class Config:
        from_attributes = True
