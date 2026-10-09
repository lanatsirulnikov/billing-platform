import uuid
from datetime import datetime
from decimal import Decimal

from app.db.session import Base
from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    user_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    overage_user_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    interval: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
