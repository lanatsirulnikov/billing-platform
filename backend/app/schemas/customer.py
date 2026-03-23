# app/schemas/customer.py
from datetime import datetime
from pydantic import BaseModel, EmailStr

class CustomerCreate(BaseModel):
    name: str
    email: EmailStr

class CustomerOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True