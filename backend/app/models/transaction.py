from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("payment_app", "transaction_reference", name="uq_transactions_app_reference"),
        UniqueConstraint("fingerprint", name="uq_transactions_fingerprint"),
        Index("ix_transactions_transaction_time", "transaction_time"),
        Index("ix_transactions_category_time", "category_id", "transaction_time"),
        Index("ix_transactions_merchant", "merchant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(16), default="expense", nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(24), default="manual", nullable=False)
    payment_app: Mapped[str] = mapped_column(String(24), default="other", nullable=False)
    transaction_reference: Mapped[str | None] = mapped_column(String(160))
    fingerprint: Mapped[str | None] = mapped_column(String(64))
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_notification: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category: Mapped["Category | None"] = relationship(back_populates="transactions")
