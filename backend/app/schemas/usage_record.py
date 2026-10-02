from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(from_attributes=True)
