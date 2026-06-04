"""
StockMovement model — single source of truth for all inventory changes.

Stock calculation (INSTRUCTION.md §5):
  current_stock = opening_stock + purchases_received + sales_returns
                - confirmed_sales - damages - free_items_given
                - stock_adjustments_out + stock_adjustments_in
                - dsr_issues + dsr_returns

IMPORTANT: Stock is NEVER stored on the product — always SUM(stock_movements).
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


class MovementType(str, enum.Enum):
    OPENING_STOCK   = "OPENING_STOCK"
    PURCHASE        = "PURCHASE"        # Stock in from supplier
    SALE            = "SALE"            # Stock out on invoice
    SALES_RETURN    = "SALES_RETURN"    # Returned from dealer
    DAMAGE          = "DAMAGE"          # Damaged/written off
    FREE_GIVEN      = "FREE_GIVEN"      # Free promotional items
    ADJUSTMENT_IN   = "ADJUSTMENT_IN"   # Manual correction upward
    ADJUSTMENT_OUT  = "ADJUSTMENT_OUT"  # Manual correction downward
    DSR_ISSUE       = "DSR_ISSUE"       # Stock given to DSR
    DSR_RETURN      = "DSR_RETURN"      # Stock returned from DSR


# Movements that ADD to stock
INWARD_TYPES = {
    MovementType.OPENING_STOCK,
    MovementType.PURCHASE,
    MovementType.SALES_RETURN,
    MovementType.ADJUSTMENT_IN,
    MovementType.DSR_RETURN,
}

# Movements that SUBTRACT from stock
OUTWARD_TYPES = {
    MovementType.SALE,
    MovementType.DAMAGE,
    MovementType.FREE_GIVEN,
    MovementType.ADJUSTMENT_OUT,
    MovementType.DSR_ISSUE,
}


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False,
        index=True,
    )
    movement_type: Mapped[MovementType] = mapped_column(
        SAEnum(MovementType, name="movement_type_enum"), nullable=False
    )
    # Always positive — type determines direction
    qty_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    # Cost/sell price at the time of this movement — NUMERIC(15,2)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    movement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # Reference to the source document
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="stock_movements")  # noqa: F821

    def __repr__(self) -> str:
        return f"<StockMovement type={self.movement_type} qty={self.qty_pieces}>"
