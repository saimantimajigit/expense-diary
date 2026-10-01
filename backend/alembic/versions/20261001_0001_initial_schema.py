"""Create categories, merchant rules, and transactions.

Revision ID: 20261001_0001
Revises:
Create Date: 2026-10-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20261001_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_categories_slug")),
    )
    op.create_table(
        "merchant_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_pattern", sa.String(length=160), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name=op.f("fk_merchant_rules_category_id_categories"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_merchant_rules")),
    )
    op.create_index("ix_merchant_rules_pattern_active_priority", "merchant_rules", ["merchant_pattern", "is_active", "priority"])
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("transaction_type", sa.String(length=16), nullable=False),
        sa.Column("merchant", sa.String(length=200), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=24), nullable=False),
        sa.Column("payment_app", sa.String(length=24), nullable=False),
        sa.Column("transaction_reference", sa.String(length=160), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
        sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_notification", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name=op.f("fk_transactions_category_id_categories"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.UniqueConstraint("payment_app", "transaction_reference", name="uq_transactions_app_reference"),
        sa.UniqueConstraint("fingerprint", name="uq_transactions_fingerprint"),
    )
    op.create_index("ix_transactions_transaction_time", "transactions", ["transaction_time"])
    op.create_index("ix_transactions_category_time", "transactions", ["category_id", "transaction_time"])
    op.create_index("ix_transactions_merchant", "transactions", ["merchant"])


def downgrade() -> None:
    op.drop_index("ix_transactions_merchant", table_name="transactions")
    op.drop_index("ix_transactions_category_time", table_name="transactions")
    op.drop_index("ix_transactions_transaction_time", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_merchant_rules_pattern_active_priority", table_name="merchant_rules")
    op.drop_table("merchant_rules")
    op.drop_table("categories")
