import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SAEnum, ForeignKey,
    Integer, Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PurchaseReturnStatus(str, enum.Enum):
    DRAFT     = "DRAFT"
    CONFIRMED = "CONFIRMED"
    VOID      = "VOID"


class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    return_no: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_receivable: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    
    status: Mapped[PurchaseReturnStatus] = mapped_column(
        SAEnum(PurchaseReturnStatus, name="purchase_return_status_enum"),
        default=PurchaseReturnStatus.DRAFT, nullable=False,
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
    supplier: Mapped["Supplier"] = relationship("Supplier")  # noqa: F821
    purchase: Mapped["Purchase"] = relationship("Purchase")  # noqa: F821
    items: Mapped[list["PurchaseReturnItem"]] = relationship(
        "PurchaseReturnItem", back_populates="purchase_return", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PurchaseReturn id={self.id} status={self.status}>"


class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    purchase_return_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty_carton: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qty_pcs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    return_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    purchase_return: Mapped["PurchaseReturn"] = relationship("PurchaseReturn", back_populates="items")
    product: Mapped["Product"] = relationship("Product")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PurchaseReturnItem product={self.product_id} qty={self.total_pieces}>"
