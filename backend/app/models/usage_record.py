import uuid
from datetime import datetime, date
from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint("subscription_id", "recorded_on", name="uq_usage_records_subscription_day"),
        CheckConstraint("active_user_count >= 0", name="ck_usage_records_active_user_count_non_negative"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("subscriptions.id"), nullable=False)
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    active_user_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
