from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories import merchant_rule_repository
from app.schemas.merchant_rule import MerchantRuleCreate
from app.services.categorization_service import InvalidCategoryError
from app.services.merchant_normalization import normalize_merchant


def list_rules(session: Session):
    return merchant_rule_repository.list_active(session)


def create_or_update(session: Session, payload: MerchantRuleCreate):
    category = session.get(Category, payload.category_id)
    if category is None or not category.is_active:
        raise InvalidCategoryError("The selected category does not exist or is inactive")
    pattern = normalize_merchant(payload.merchant_pattern)
    if not pattern:
        raise ValueError("merchant_pattern must contain letters or numbers")
    return merchant_rule_repository.upsert(
        session,
        merchant_pattern=pattern,
        category_id=category.id,
        priority=payload.priority,
        is_active=payload.is_active,
    )
