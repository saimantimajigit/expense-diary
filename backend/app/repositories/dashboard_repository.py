from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction


def totals(session: Session, start: datetime, end: datetime) -> tuple[dict[str, Decimal], int]:
    rows = session.execute(
        select(Transaction.transaction_type, func.sum(Transaction.amount), func.count(Transaction.id))
        .where(Transaction.transaction_time >= start, Transaction.transaction_time < end)
        .group_by(Transaction.transaction_type)
    ).all()
    amounts = {"expense": Decimal("0.00"), "income": Decimal("0.00"), "refund": Decimal("0.00")}
    count = 0
    for transaction_type, amount, transaction_count in rows:
        if transaction_type in amounts:
            amounts[transaction_type] = amount or Decimal("0.00")
        count += transaction_count
    return amounts, count


def categories(session: Session, start: datetime, end: datetime) -> list[tuple[str, Decimal]]:
    rows = session.execute(
        select(func.coalesce(Category.name, "Other"), func.sum(Transaction.amount))
        .select_from(Transaction)
        .outerjoin(Transaction.category)
        .where(
            Transaction.transaction_time >= start,
            Transaction.transaction_time < end,
            Transaction.transaction_type == "expense",
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc(), func.coalesce(Category.name, "Other"))
    ).all()
    return [(category, amount or Decimal("0.00")) for category, amount in rows]
