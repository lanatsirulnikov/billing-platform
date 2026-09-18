from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.subscription import Subscription
from app.schemas.invoice_item import InvoiceItemCreate, InvoiceItemOut

router = APIRouter(prefix="/invoice-items", tags=["invoice-items"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=InvoiceItemOut)
def create_invoice_item(input: InvoiceItemCreate, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, input.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="INVOICE_NOT_FOUND")

    if input.subscription_id:
        subscription = db.get(Subscription, input.subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="SUBSCRIPTION_NOT_FOUND")
        
    if input.quantity <= 0:
        raise HTTPException(status_code=400, detail="INVALID_QUANTITY")
    
    if input.period_start and input.period_end and input.period_end < input.period_start:
        raise HTTPException(status_code=400, detail="INVALID_BILLING_PERIOD")
    
    expected_amount = input.unit_price * input.quantity
    if input.amount != expected_amount:
        raise HTTPException(status_code=400, detail="INVALID_INVOICE_ITEM_AMOUNT")

    item = InvoiceItem(
        invoice_id=input.invoice_id,
        subscription_id=input.subscription_id,
        item_type=input.item_type,
        description=input.description,
        period_start=input.period_start,
        period_end=input.period_end,
        quantity=input.quantity,
        unit_price=input.unit_price,
        amount=input.amount,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/{item_id}", response_model=InvoiceItemOut)
def get_invoice_item(item_id: str, db: Session = Depends(get_db)):
    item = db.get(InvoiceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="INVOICE_ITEM_NOT_FOUND")
    return item
