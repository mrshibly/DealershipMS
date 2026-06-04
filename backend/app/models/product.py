"""
Product model.

Key rules (INSTRUCTION.md §3, §5):
- All prices stored as NUMERIC(15,2) — never float
- Quantities in INTEGER (pieces). Cartons = qty_pieces / pcs_per_carton
- Stock is NOT stored here — computed via SUM(stock_movements) at query time
- Barcode is Code128, auto-generated on create
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name_en: Mapped[str] = mapped_column(String(300), nullable=False)
    name_bn: Mapped[str | None] = mapped_column(String(300), nullable=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    # Unit of measure: piece, kg, litre, set
    unit: Mapped[str] = mapped_column(String(20), default="piece", nullable=False)
    # How many pieces in one carton
    pcs_per_carton: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # All prices — NUMERIC(15,2) — never float
    buy_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sell_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    mrp: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    # VAT
    vat_applicable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("15.00"), nullable=False
    )
    # Low stock alert threshold (in pieces)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
    category: Mapped["Category"] = relationship("Category", back_populates="products")  # noqa: F821
    stock_movements: Mapped[list["StockMovement"]] = relationship(  # noqa: F821
        "StockMovement", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product sku={self.sku!r} name={self.name_en!r}>"
