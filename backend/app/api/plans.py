from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanOut

router = APIRouter(prefix="/plans", tags=["plans"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=PlanOut)
def create_plan(input: PlanCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Plan).where(Plan.name == input.name))
    if existing:
        raise HTTPException(status_code=400, detail="PLAN_NAME_EXISTS")

    plan = Plan(
        name=input.name,
        price=input.price,
        user_quota=input.user_quota,
        overage_user_price=input.overage_user_price,
        interval=input.interval
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.scalars(select(Plan).order_by(Plan.created_at.desc())).all()


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="PLAN_NOT_FOUND")
    return plan


@router.delete("/{plan_id}")
def delete_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="PLAN_NOT_FOUND")
    db.delete(plan)
    db.commit()
    return {"ok": True}
