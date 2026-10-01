from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


def get(session: Session, category_id: int) -> Category | None:
    return session.get(Category, category_id)


def get_by_slug(session: Session, slug: str) -> Category | None:
    return session.scalar(select(Category).where(Category.slug == slug))


def list_active(session: Session) -> list[Category]:
    return list(session.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.name)))
