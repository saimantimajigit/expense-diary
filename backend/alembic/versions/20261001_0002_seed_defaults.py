"""Seed default categories and merchant rules.

Revision ID: 20261001_0002
Revises: 20261001_0001
Create Date: 2026-10-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20261001_0002"
down_revision = "20261001_0001"
branch_labels = None
depends_on = None

CATEGORIES = [
    ("Food", "food"),
    ("Groceries", "groceries"),
    ("Transport", "transport"),
    ("Shopping", "shopping"),
    ("Bills", "bills"),
    ("Healthcare", "healthcare"),
    ("Entertainment", "entertainment"),
    ("Subscription", "subscription"),
    ("Work", "work"),
    ("Family", "family"),
    ("Other", "other"),
]

RULES = [
    ("swiggy", "food"),
    ("zomato", "food"),
    ("uber", "transport"),
    ("ola", "transport"),
    ("amazon", "shopping"),
    ("flipkart", "shopping"),
    ("netflix", "subscription"),
]


def upgrade() -> None:
    connection = op.get_bind()
    for name, slug in CATEGORIES:
        connection.execute(
            sa.text("INSERT INTO categories (name, slug, is_active) VALUES (:name, :slug, :active)"),
            {"name": name, "slug": slug, "active": True},
        )
    for pattern, slug in RULES:
        connection.execute(
            sa.text(
                "INSERT INTO merchant_rules (merchant_pattern, category_id, priority, is_active) "
                "SELECT :pattern, id, :priority, :active FROM categories WHERE slug = :slug"
            ),
            {"pattern": pattern, "priority": 100, "active": True, "slug": slug},
        )


def downgrade() -> None:
    connection = op.get_bind()
    for pattern, _ in RULES:
        connection.execute(sa.text("DELETE FROM merchant_rules WHERE merchant_pattern = :pattern"), {"pattern": pattern})
    for _, slug in CATEGORIES:
        connection.execute(sa.text("DELETE FROM categories WHERE slug = :slug"), {"slug": slug})
