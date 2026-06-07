"""
Collection model.

Records payments received from dealers/shops against invoices.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, Enum as SAEnum, ForeignKey,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentMethod(str, enum.Enum):
    CASH          = "CASH"
    BKASH         = "BKASH"
    NAGAD         = "NAGAD"
    ROCKET        = "ROCKET"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE        = "CHEQUE"


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=True,
        index=True,
    )
    dealer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dealers.id", ondelete="RESTRICT"), nullable=True,
        index=True,
    )
    dsr_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dsrs.id", ondelete="RESTRICT"), nullable=True,
        index=True,
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True,
        index=True,
    )
    
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method_enum", create_type=False),
        nullable=False,
    )
    reference_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="collections")  # noqa: F821
    dealer: Mapped["Dealer"] = relationship("Dealer")  # noqa: F821
    dsr: Mapped["DSR"] = relationship("DSR")  # noqa: F821
    account: Mapped["Account"] = relationship("Account")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Collection amount={self.amount} method={self.payment_method}>"
