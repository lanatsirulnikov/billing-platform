import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Numeric
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    customer_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("customers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
