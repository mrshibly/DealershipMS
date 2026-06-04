"""
Alembic migration 0002 — Products, Inventory & Suppliers tables.

Tables created:
  categories, suppliers, products, stock_movements,
  purchases, purchase_items
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_products_inventory"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ENUMS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TYPE movement_type_enum AS ENUM (
            'OPENING_STOCK','PURCHASE','SALE','SALES_RETURN',
            'DAMAGE','FREE_GIVEN','ADJUSTMENT_IN','ADJUSTMENT_OUT',
            'DSR_ISSUE','DSR_RETURN'
        )
    """)
    op.execute("""
        CREATE TYPE purchase_status_enum AS ENUM (
            'DRAFT','RECEIVED','CANCELLED'
        )
    """)

    # ------------------------------------------------------------------
    # CATEGORIES
    # ------------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_bn", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # SUPPLIERS
    # ------------------------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("contact_person", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("vat_no", sa.String(50), nullable=True),
        sa.Column("bank_name", sa.String(200), nullable=True),
        sa.Column("bank_account", sa.String(50), nullable=True),
        sa.Column("opening_balance", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # PRODUCTS
    # ------------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name_en", sa.String(300), nullable=False),
        sa.Column("name_bn", sa.String(300), nullable=True),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("barcode", sa.String(100), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("unit", sa.String(20), nullable=False, server_default="piece"),
        sa.Column("pcs_per_carton", sa.Integer, nullable=False, server_default="1"),
        sa.Column("buy_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("sell_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(15, 2), nullable=True),
        sa.Column("vat_applicable", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("vat_rate", sa.Numeric(5, 2), nullable=False, server_default="15.00"),
        sa.Column("low_stock_threshold", sa.Integer, nullable=False, server_default="0"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
        sa.UniqueConstraint("barcode"),
    )
    op.create_index("ix_products_barcode", "products", ["barcode"])
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_category_id", "products", ["category_id"])

    # ------------------------------------------------------------------
    # STOCK MOVEMENTS
    # ------------------------------------------------------------------
    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", postgresql.ENUM(
            "OPENING_STOCK","PURCHASE","SALE","SALES_RETURN",
            "DAMAGE","FREE_GIVEN","ADJUSTMENT_IN","ADJUSTMENT_OUT",
            "DSR_ISSUE","DSR_RETURN", name="movement_type_enum", create_type=False
        ), nullable=False),
        sa.Column("qty_pieces", sa.Integer, nullable=False),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("movement_date", sa.Date, nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("requires_approval", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_index("ix_stock_movements_date", "stock_movements", ["movement_date"])

    # ------------------------------------------------------------------
    # PURCHASES
    # ------------------------------------------------------------------
    op.create_table(
        "purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("purchase_date", sa.Date, nullable=False),
        sa.Column("invoice_no", sa.String(100), nullable=True),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("vat_amount", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("discount", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("total", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("paid", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("status", postgresql.ENUM("DRAFT","RECEIVED","CANCELLED", name="purchase_status_enum", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchases_supplier_id", "purchases", ["supplier_id"])
    op.create_index("ix_purchases_date", "purchases", ["purchase_date"])

    # ------------------------------------------------------------------
    # PURCHASE ITEMS
    # ------------------------------------------------------------------
    op.create_table(
        "purchase_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qty_carton", sa.Integer, nullable=False, server_default="0"),
        sa.Column("qty_pcs", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_pieces", sa.Integer, nullable=False),
        sa.Column("buy_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(15, 2), nullable=False),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_items_purchase_id", "purchase_items", ["purchase_id"])


def downgrade() -> None:
    op.drop_table("purchase_items")
    op.drop_table("purchases")
    op.drop_index("ix_stock_movements_date")
    op.drop_index("ix_stock_movements_product_id")
    op.drop_table("stock_movements")
    op.drop_index("ix_products_category_id")
    op.drop_index("ix_products_sku")
    op.drop_index("ix_products_barcode")
    op.drop_table("products")
    op.drop_table("suppliers")
    op.drop_table("categories")
    op.execute("DROP TYPE IF EXISTS purchase_status_enum")
    op.execute("DROP TYPE IF EXISTS movement_type_enum")
