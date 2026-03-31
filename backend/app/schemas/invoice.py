from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: str
    status: Literal["draft", "open", "paid", "void"] = "draft"
    subtotal: float
    tax_amount: float = 0
    total_amount: float
    currency: str = "USD"
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    due_date: date
    issued_at:Optional[datetime] = None
    paid_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None

class InvoiceOut(BaseModel):
    id: str
    invoice_number: str
    customer_id: str
    status: str
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str
    billing_period_start: Optional[date]
    billing_period_end: Optional[date]
    due_date: date
    issued_at: Optional[datetime]
    paid_at: Optional[datetime]
    voided_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
