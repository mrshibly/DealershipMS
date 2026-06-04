"""
DSR (Dealer Sales Representative) model.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DSR(Base):
    __tablename__ = "dsrs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    route: Mapped["Route"] = relationship("Route", back_populates="dsrs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DSR name={self.name!r} phone={self.phone!r}>"
