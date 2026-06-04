"""
Alembic migration 0003 — People and Routes tables.

Tables created:
  routes, dealers, dsrs, shops
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_people_routes"
down_revision: Union[str, None] = "0002_products_inventory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------
    op.create_table(
        "routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("area", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ------------------------------------------------------------------
    # DEALERS
    # ------------------------------------------------------------------
    op.create_table(
        "dealers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("owner_name", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("upazila", sa.String(100), nullable=True),
        sa.Column("trade_license", sa.String(100), nullable=True),
        sa.Column("nid", sa.String(50), nullable=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("ix_dealers_phone", "dealers", ["phone"])
    op.create_index("ix_dealers_route_id", "dealers", ["route_id"])

    # ------------------------------------------------------------------
    # DSRS
    # ------------------------------------------------------------------
    op.create_table(
        "dsrs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("nid", sa.String(50), nullable=True),
        sa.Column("photo", sa.Text, nullable=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("joining_date", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("ix_dsrs_phone", "dsrs", ["phone"])
    op.create_index("ix_dsrs_route_id", "dsrs", ["route_id"])

    # ------------------------------------------------------------------
    # SHOPS
    # ------------------------------------------------------------------
    op.create_table(
        "shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("dealer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("owner_name", sa.String(200), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("shop_type", sa.String(50), nullable=False, server_default="Retailer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dealer_id"], ["dealers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shops_dealer_id", "shops", ["dealer_id"])


def downgrade() -> None:
    op.drop_table("shops")
    op.drop_table("dsrs")
    op.drop_table("dealers")
    op.drop_table("routes")
