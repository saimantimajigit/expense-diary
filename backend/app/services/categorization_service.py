from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.merchant_rule import MerchantRule
from app.services.merchant_normalization import normalize_merchant


class InvalidCategoryError(Exception):
    pass


def categorize(session: Session, merchant: str | None, explicit_category_id: int | None = None) -> int:
    if explicit_category_id is not None:
        category = session.get(Category, explicit_category_id)
        if category is None or not category.is_active:
            raise InvalidCategoryError("The selected category does not exist or is inactive")
        return category.id

    merchant_key = normalize_merchant(merchant)
    if merchant_key:
        rules = session.scalars(
            select(MerchantRule)
            .join(MerchantRule.category)
            .where(MerchantRule.is_active.is_(True), Category.is_active.is_(True))
            .order_by(MerchantRule.priority.asc(), MerchantRule.id.asc())
        )
        for rule in rules:
            pattern = normalize_merchant(rule.merchant_pattern)
            if pattern and pattern in merchant_key:
                return rule.category_id

    fallback = session.scalar(select(Category).where(Category.slug == "other", Category.is_active.is_(True)))
    if fallback is None:
        raise RuntimeError("Default category 'Other' is missing; run database migrations")
    return fallback.id
