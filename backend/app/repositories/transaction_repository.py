from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.transaction import Transaction


def create(session: Session, values: dict[str, object]) -> Transaction:
    transaction = Transaction(**values)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def get(session: Session, transaction_id: int) -> Transaction | None:
    return session.scalar(
        select(Transaction).options(joinedload(Transaction.category)).where(Transaction.id == transaction_id)
    )


def list_transactions(
    session: Session,
    *,
    start_date: datetime | None,
    end_date: datetime | None,
    category: str | None,
    payment_app: str | None,
    merchant: str | None,
    transaction_type: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Transaction], int]:
    filters = []
    if start_date is not None:
        filters.append(Transaction.transaction_time >= start_date)
    if end_date is not None:
        filters.append(Transaction.transaction_time <= end_date)
    if category is not None:
        filters.append(Category.slug == category.strip().lower())
    if payment_app is not None:
        filters.append(Transaction.payment_app == payment_app)
    if merchant is not None:
        filters.append(Transaction.merchant.ilike(f"%{merchant.strip()}%"))
    if transaction_type is not None:
        filters.append(Transaction.transaction_type == transaction_type)

    statement = select(Transaction).outerjoin(Transaction.category).options(joinedload(Transaction.category))
    count_statement = select(func.count(Transaction.id)).select_from(Transaction).outerjoin(Transaction.category)
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)

    items = list(
        session.scalars(
            statement.order_by(Transaction.transaction_time.desc(), Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        ).unique()
    )
    total = session.scalar(count_statement) or 0
    return items, total


def update(session: Session, transaction_id: int, values: dict[str, object]) -> Transaction | None:
    transaction = get(session, transaction_id)
    if transaction is None:
        return None
    for key, value in values.items():
        setattr(transaction, key, value)
    if "category_id" in values:
        session.expire(transaction, ["category"])
    session.commit()
    return get(session, transaction_id)


def get_by_fingerprint(session: Session, fingerprint: str) -> Transaction | None:
    return session.scalar(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.fingerprint == fingerprint)
    )


def delete(session: Session, transaction_id: int) -> bool:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None:
        return False
    session.delete(transaction)
    session.commit()
    return True
