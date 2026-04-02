from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.customer import Customer
from app.models.subscription import Subscription
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceDetailOut
from app.schemas.invoice_item import InvoiceItemOut

router = APIRouter(prefix="/invoices", tags=["invoices"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=InvoiceOut)
def create_invoice(input: InvoiceCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, input.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="CUSTOMER_NOT_FOUND")
    
    invoice = Invoice(
        invoice_number=input.invoice_number,
        customer_id=input.customer_id,
        status=input.status,
        subtotal=input.subtotal,
        tax_amount=input.tax_amount,
        total_amount=input.total_amount,
        currency=input.currency,
        billing_period_start=input.billing_period_start,
        billing_period_end=input.billing_period_end,
        due_date=input.due_date,
        issued_at=input.issued_at,
        paid_at=input.paid_at,
        voided_at=input.voided_at,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.scalars(select(Invoice).order_by(Invoice.created_at.desc())).all()

@router.get("/{invoice_id}", response_model=InvoiceDetailOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="INVOICE_NOT_FOUND")
    
    customer = db.get(Customer, invoice.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="CUSTOMER_NOT_FOUND")
    
    items = db.scalars(
        select(InvoiceItem)
        .where(InvoiceItem.invoice_id == invoice_id)
        .order_by(InvoiceItem.created_at.asc())
    ).all()

    item_details = []
    for item in items:
        subscription = None
        if item.subscription_id:
            subscription = db.get(Subscription, item.subscription_id)

        item_details.append({
            "id": item.id,
            "invoice_id": item.invoice_id,
            "subscription_id": item.subscription_id,
            "item_type": item.item_type,
            "description": item.description,
            "period_start": item.period_start,
            "period_end": item.period_end,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "amount": item.amount,
            "created_at": item.created_at,
            "subscription": subscription,
        })

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "customer_id": invoice.customer_id,
        "status": invoice.status,
        "subtotal": invoice.subtotal,
        "tax_amount": invoice.tax_amount,
        "total_amount": invoice.total_amount,
        "currency": invoice.currency,
        "billing_period_start": invoice.billing_period_start,
        "billing_period_end": invoice.billing_period_end,
        "due_date": invoice.due_date,
        "issued_at": invoice.issued_at,
        "paid_at": invoice.paid_at,
        "voided_at": invoice.voided_at,
        "created_at": invoice.created_at,
        "customer": customer,
        "items": item_details,
    }

@router.get("/{invoice_id}/items", response_model=list[InvoiceItemOut])
def list_invoice_items(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="INVOICE_NOT_FOUND")

    return db.scalars(
        select(InvoiceItem)
        .where(InvoiceItem.invoice_id == invoice_id)
        .order_by(InvoiceItem.created_at.asc())
    ).all()