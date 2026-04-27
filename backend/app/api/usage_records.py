from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.usage_record import UsageRecord
from app.schemas.usage_record import UsageRecordCreate, UsageRecordOut
from app.models.subscription import Subscription

router = APIRouter(prefix="/usage-records", tags=["usage-records"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=UsageRecordOut)
def create_usage_record(input: UsageRecordCreate, db: Session = Depends(get_db)):
    subscription_exists = db.scalar(select(UsageRecord).where(UsageRecord.subscription_id == input.subscription_id))
    if not subscription_exists:
        raise HTTPException(status_code=404, detail="SUBSCRIPTION_NOT_FOUND")
    
    subscription = db.get(Subscription, input.subscription_id)

    if subscription.status == "cancelled" and input.recorded_on >= subscription.next_billing_date:
        raise HTTPException(status_code=400, detail="SUBSCRIPTION_CANCELLED")
    
    existing = db.scalar(
        select(UsageRecord).where(
            UsageRecord.subscription_id == input.subscription_id,
            UsageRecord.recorded_on == input.recorded_on,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="USAGE_RECORD_EXISTS")
    usage_record = UsageRecord(
        subscription_id=input.subscription_id,
        recorded_on=input.recorded_on,
        active_user_count=input.active_user_count,
    )
    db.add(usage_record)
    db.commit()
    db.refresh(usage_record)
    return usage_record

@router.get("", response_model=list[UsageRecordOut])
def list_usage_records(db: Session = Depends(get_db)):
    return db.scalars(select(UsageRecord).order_by(UsageRecord.created_at.desc())).all()