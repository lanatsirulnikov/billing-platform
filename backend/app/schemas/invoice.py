from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: str
    status: Literal["draft", "open", "paid", "void"] = "draft"
    amount: float
    due_date: date


class InvoiceOut(BaseModel):
    id: str
    invoice_number: str
    customer_id: str
    status: str
    amount: float
    due_date: date
    created_at: datetime

    class Config:
        from_attributes = True
