from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.billing_investigation import InvoiceIncreaseOut, InvoiceIncreaseIn
from app.services.billing_investigation import (
    InvoiceInvestigationInvalidInput,
    InvoiceInvestigationNotFound,
    investigate_invoice_increase,
)
from app.api.customers import get_db

router = APIRouter(prefix="/billing-investigations", tags=["billing-investigations"])

@router.post("/invoice-increase", response_model=InvoiceIncreaseOut)
def invoice_increase(input: InvoiceIncreaseIn, db: Session = Depends(get_db)):
    try:
        return investigate_invoice_increase(db, input)
    except InvoiceInvestigationNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvoiceInvestigationInvalidInput as e:
        raise HTTPException(status_code=400, detail=str(e))