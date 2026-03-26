# app/api/customers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=SubscriptionOut)
def create_subscription(input: SubscriptionCreate, db: Session = Depends(get_db)):
    subscription = Subscription(
        customer_id=input.customer_id,
        plan_id=input.plan_id,
        status=input.status,
        start_date=input.start_date,
        end_date=input.end_date,
        user_quota_override=input.user_quota_override
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(db: Session = Depends(get_db)):
    return db.scalars(select(Subscription).order_by(Subscription.created_at.desc())).all()

@router.get("/{subscription_id}", response_model=SubscriptionOut)
def get_subscription(subscription_id: str, db: Session = Depends(get_db)):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="SUBSCRIPTION_NOT_FOUND")
    return subscription