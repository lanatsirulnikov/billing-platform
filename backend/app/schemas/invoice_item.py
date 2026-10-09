from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class InvoiceItemCreate(BaseModel):
    invoice_id: str
    subscription_id: Optional[str] = None
    item_type: Literal["subscription_base", "usage_overage", "addon", "manual_adjustment"]
    description: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    quantity: int
    unit_price: Decimal
    amount: Decimal


class InvoiceItemOut(BaseModel):
    id: str
    invoice_id: str
    subscription_id: Optional[str]
    item_type: str
    description: str
    period_start: Optional[date]
    period_end: Optional[date]
    quantity: int
    unit_price: Decimal
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceItemSubscriptionOut(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class InvoiceItemDetailOut(InvoiceItemOut):
    subscription: Optional[InvoiceItemSubscriptionOut] = None
