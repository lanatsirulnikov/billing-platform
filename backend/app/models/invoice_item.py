from decimal import Decimal
from typing import Optional
import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("invoices.id"), nullable=False)
    subscription_id: Mapped[Optional[str]] = mapped_column(CHAR(36), ForeignKey("subscriptions.id"), nullable=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    invoice = relationship("Invoice", back_populates="items")

