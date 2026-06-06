"""
Target model for DSR sales targets.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    dsr_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dsrs.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_month: Mapped[date] = mapped_column(Date, nullable=False) # e.g. 2026-06-01 for June 2026
    target_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    
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
    dsr: Mapped["DSR"] = relationship("DSR")

    def __repr__(self) -> str:
        return f"<Target dsr_id={self.dsr_id!r} month={self.target_month!r} amount={self.target_amount!r}>"
