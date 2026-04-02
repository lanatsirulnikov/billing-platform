from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel
from app.schemas.invoice_item import InvoiceItemOut, InvoiceItemDetailOut

class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: str
    status: Literal["draft", "open", "paid", "void"] = "draft"
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
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
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
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

class InvoiceCustomerOut(BaseModel):
    id: str
    name: str
    email: str

    class Config:
        from_attributes = True


class InvoiceDetailOut(InvoiceOut):
    customer: InvoiceCustomerOut
    items: list[InvoiceItemDetailOut]
