from datetime import datetime
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.repositories import transaction_repository
from app.schemas.transaction import TransactionCreate, TransactionIngest, TransactionUpdate
from app.services.categorization_service import categorize
from app.services.deduplication_service import find_duplicate, prepare_fingerprint


class TransactionConflictError(Exception):
    pass


def create(session: Session, payload: TransactionCreate) -> Transaction:
    values = payload.model_dump()
    if values["merchant"] is not None:
        values["merchant"] = values["merchant"].strip() or None
    values["category_id"] = categorize(session, values["merchant"], values["category_id"])
    if values["transaction_reference"] and find_duplicate(session, values) is not None:
        raise TransactionConflictError("A transaction with this payment reference already exists")
    try:
        return transaction_repository.create(session, values)
    except IntegrityError as error:
        session.rollback()
        if values["transaction_reference"] and find_duplicate(session, values) is not None:
            raise TransactionConflictError("A transaction with this payment reference already exists") from error
        raise


def ingest(session: Session, payload: TransactionIngest) -> tuple[Transaction, bool]:
    values = payload.model_dump()
    values["merchant"] = values["merchant"].strip() or None if values["merchant"] else None
    values["raw_notification"] = sanitize_raw_notification(values["raw_notification"])
    values["raw_payload"] = sanitize_raw_payload(values["raw_payload"])

    duplicate = find_duplicate(session, values)
    if duplicate is not None:
        return duplicate, True

    values["category_id"] = categorize(session, values["merchant"], values["category_id"])
    if not values["transaction_reference"]:
        values["fingerprint"] = prepare_fingerprint(values)
    try:
        return transaction_repository.create(session, values), False
    except IntegrityError:
        session.rollback()
        duplicate = find_duplicate(session, values)
        if duplicate is not None:
            return duplicate, True
        raise


def sanitize_raw_notification(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = "".join(character for character in value if character in "\n\r\t" or character.isprintable())
    return cleaned[:2000]


def sanitize_raw_payload(value: dict[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    allowed_keys = {"packageName", "title", "text", "bigText", "subText", "postTime"}
    sanitized: dict[str, object] = {}
    for key in allowed_keys & value.keys():
        item = value[key]
        if key == "postTime" and isinstance(item, int) and not isinstance(item, bool) and abs(item) < 10**16:
            sanitized[key] = item
        elif key != "postTime" and isinstance(item, str):
            cleaned = "".join(character for character in item if character in "\n\r\t" or character.isprintable())
            sanitized[key] = cleaned[:1000]
    return sanitized


def get(session: Session, transaction_id: int) -> Transaction | None:
    return transaction_repository.get(session, transaction_id)


def list_transactions(
    session: Session,
    *,
    start_date: datetime | None,
    end_date: datetime | None,
    category: str | None,
    payment_app: Literal["gpay", "phonepe", "paytm", "other"] | None,
    merchant: str | None,
    transaction_type: Literal["expense", "income", "refund"] | None,
    limit: int,
    offset: int,
) -> tuple[list[Transaction], int]:
    return transaction_repository.list_transactions(
        session,
        start_date=start_date,
        end_date=end_date,
        category=category,
        payment_app=payment_app,
        merchant=merchant,
        transaction_type=transaction_type,
        limit=limit,
        offset=offset,
    )


def update(session: Session, transaction_id: int, payload: TransactionUpdate) -> Transaction | None:
    values = payload.model_dump(exclude_unset=True)
    existing = transaction_repository.get(session, transaction_id)
    if existing is None:
        return None
    if "merchant" in values and values["merchant"] is not None:
        values["merchant"] = values["merchant"].strip() or None
    if "category_id" in values:
        if values["category_id"] is not None:
            values["category_id"] = categorize(session, values.get("merchant", existing.merchant), values["category_id"])
    elif "merchant" in values:
        values["category_id"] = categorize(session, values["merchant"])
    return transaction_repository.update(session, transaction_id, values)


def delete(session: Session, transaction_id: int) -> bool:
    return transaction_repository.delete(session, transaction_id)
