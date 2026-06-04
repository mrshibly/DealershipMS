"""
Purchase and PurchaseItem models.

Financial write operations (purchase receipt + stock) must be in one DB transaction.
All amounts stored as NUMERIC(15,2).
"""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SAEnum, ForeignKey,
    Integer, Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PurchaseStatus(str, enum.Enum):
    DRAFT     = "DRAFT"
    RECEIVED  = "RECEIVED"
    CANCELLED = "CANCELLED"


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True,
        index=True,
    )
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    invoice_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # All amounts — NUMERIC(15,2)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    status: Mapped[PurchaseStatus] = mapped_column(
        SAEnum(PurchaseStatus, name="purchase_status_enum"),
        default=PurchaseStatus.DRAFT, nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchases")  # noqa: F821
    items: Mapped[list["PurchaseItem"]] = relationship(
        "PurchaseItem", back_populates="purchase", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Purchase id={self.id} status={self.status}>"


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty_carton: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qty_pcs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Total pieces = (qty_carton * pcs_per_carton) + qty_pcs — computed in service
    total_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    # Buy price at time of purchase — NUMERIC(15,2)
    buy_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")
    product: Mapped["Product"] = relationship("Product")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PurchaseItem product={self.product_id} qty={self.total_pieces}>"
