"""
Role model — RBAC roles with JSONB permissions.

Permissions JSONB structure:
{
    "invoices":   { "view": true,  "create": true,  "update": false, "delete": false },
    "products":   { "view": true,  "create": false, "update": false, "delete": false },
    ...
}
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func, text, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Default permission sets for seeded roles
DEFAULT_PERMISSIONS_SUPER_ADMIN: dict = {
    module: {"view": True, "create": True, "update": True, "delete": True}
    for module in [
        "dashboard", "products", "inventory", "suppliers", "purchases",
        "dealers", "shops", "dsrs", "routes", "invoices", "collections",
        "accounts", "expenses", "contra", "reports", "settings",
        "targets", "returns", "users", "roles",
    ]
}

DEFAULT_PERMISSIONS_ADMIN: dict = {
    module: {"view": True, "create": True, "update": True, "delete": False}
    for module in [
        "dashboard", "products", "inventory", "suppliers", "purchases",
        "dealers", "shops", "dsrs", "routes", "invoices", "collections",
        "accounts", "expenses", "contra", "reports", "targets", "returns",
    ]
}

DEFAULT_PERMISSIONS_STAFF: dict = {
    "dashboard": {"view": True, "create": False, "update": False, "delete": False},
    "invoices":  {"view": True, "create": True,  "update": False, "delete": False},
    "collections": {"view": True, "create": True, "update": False, "delete": False},
    "products":  {"view": True, "create": False, "update": False, "delete": False},
    "dealers":   {"view": True, "create": False, "update": False, "delete": False},
}

DEFAULT_PERMISSIONS_DSR: dict = {
    "dashboard":   {"view": True,  "create": False, "update": False, "delete": False},
    "invoices":    {"view": True,  "create": False, "update": False, "delete": False},
    "collections": {"view": True,  "create": True,  "update": False, "delete": False},
}


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship back to users
    users: Mapped[list["User"]] = relationship("User", back_populates="role")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Role name={self.name!r}>"
