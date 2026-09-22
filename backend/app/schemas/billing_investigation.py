from decimal import Decimal

from pydantic import BaseModel


class InvoiceIncreaseIn(BaseModel):
    customer_id: str
    current_invoice_id: str
    previous_invoice_id: str

class InvoiceIncreaseOut(BaseModel):
    summary: str
    current_total: Decimal
    previous_total: Decimal
    difference: Decimal
    facts: list[str]
    tool_calls: list[str]