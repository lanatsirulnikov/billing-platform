# app/schemas/customer.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr


class CustomerOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
