from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.merchant_rule import MerchantRule


def list_active(session: Session) -> list[MerchantRule]:
    return list(
        session.scalars(
            select(MerchantRule)
            .where(MerchantRule.is_active.is_(True))
            .order_by(MerchantRule.priority, MerchantRule.merchant_pattern)
        )
    )


def upsert(
    session: Session,
    *,
    merchant_pattern: str,
    category_id: int,
    priority: int,
    is_active: bool,
) -> MerchantRule:
    existing = session.scalar(
        select(MerchantRule).where(MerchantRule.merchant_pattern == merchant_pattern)
    )
    if existing is None:
        existing = MerchantRule(
            merchant_pattern=merchant_pattern,
            category_id=category_id,
            priority=priority,
            is_active=is_active,
        )
        session.add(existing)
    else:
        existing.category_id = category_id
        existing.priority = priority
        existing.is_active = is_active
    session.commit()
    session.refresh(existing)
    return existing
