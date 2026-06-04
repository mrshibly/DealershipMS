"""
Supplier model.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vat_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Opening balance owed to supplier — NUMERIC(15,2), never float
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    purchases: Mapped[list["Purchase"]] = relationship("Purchase", back_populates="supplier")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Supplier name={self.name!r}>"
