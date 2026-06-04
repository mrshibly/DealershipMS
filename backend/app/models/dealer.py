"""
Dealer model representing distributor customers.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dealer(Base):
    __tablename__ = "dealers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upazila: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trade_license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
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
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="dealers")  # noqa: F821
    shops: Mapped[list["Shop"]] = relationship("Shop", back_populates="dealer")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Dealer name={self.name!r} phone={self.phone!r}>"
