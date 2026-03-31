from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel


class InvoiceItemCreate(BaseModel):
    invoice_id: str
    subscription_id: Optional[str] = None
    item_type: Literal["subscription_base", "usage_overage", "addon", "manual_adjustment"]
    description: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    quantity: int
    unit_price: float
    amount: float


class InvoiceItemOut(BaseModel):
    id: str
    invoice_id: str
    subscription_id: Optional[str]
    item_type: str
    description: str
    period_start: Optional[date]
    period_end: Optional[date]
    quantity: int
    unit_price: float
    amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True
