# app/api/customers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=CustomerOut)
def create_customer(input: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Customer).where(Customer.email == input.email))
    if existing:
        raise HTTPException(status_code=400, detail="CUSTOMER_EMAIL_EXISTS")
    customer = Customer(name=input.name, email=input.email)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.scalars(select(Customer).order_by(Customer.created_at.desc())).all()