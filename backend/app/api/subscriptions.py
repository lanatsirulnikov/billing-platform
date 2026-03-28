# app/api/customers.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut, SubscriptionStatusUpdate

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_valid_status_transition(current_status: str, new_status: str) -> bool:
    allowed = {
        "active": {"paused", "cancelled"},
        "paused": {"active", "cancelled"},
        "cancelled": set(),
    }
    return new_status in allowed[current_status]

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

@router.patch("/{subscription_id}/status", response_model=SubscriptionOut)
def update_subscription_status(
    subscription_id: str,
    input: SubscriptionStatusUpdate,
    db: Session = Depends(get_db),
):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="SUBSCRIPTION_NOT_FOUND")

    if not is_valid_status_transition(subscription.status, input.status):
        raise HTTPException(status_code=400, detail="INVALID_STATUS_TRANSITION")

    subscription.status = input.status

    if input.status == "cancelled" and subscription.end_date is None:
        subscription.end_date = date.today()

    db.commit()
    db.refresh(subscription)
    return subscription
