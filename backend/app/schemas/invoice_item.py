from datetime import datetime
from pydantic import BaseModel


class InvoiceItemCreate(BaseModel):
    invoice_id: str
    description: str
    quantity: int
    unit_price: float
    amount: float


class InvoiceItemOut(BaseModel):
    id: str
    invoice_id: str
    description: str
    quantity: int
    unit_price: float
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True
