"""
Shop model representing retail/wholesale outlets.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    dealer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dealers.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    shop_type: Mapped[str] = mapped_column(String(50), default="Retailer", nullable=False)  # Retailer / Wholesaler
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    dealer: Mapped["Dealer"] = relationship("Dealer", back_populates="shops")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Shop name={self.name!r} dealer_id={self.dealer_id!r}>"
