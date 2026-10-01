import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction
from app.services.merchant_normalization import normalize_merchant


def transaction_fingerprint(
    *,
    payment_app: str,
    amount: Decimal,
    merchant: str | None,
    transaction_time: datetime,
    transaction_type: str,
) -> str:
    timestamp = transaction_time.astimezone(timezone.utc).timestamp()
    rounded_timestamp = round(timestamp / 10) * 10
    fingerprint_data = {
        "payment_app": payment_app,
        "amount": format(amount.quantize(Decimal("0.01")), "f"),
        "merchant": normalize_merchant(merchant),
        "transaction_time": int(rounded_timestamp),
        "transaction_type": transaction_type,
    }
    encoded = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def find_duplicate(session: Session, values: dict[str, object]) -> Transaction | None:
    payment_app = str(values["payment_app"])
    reference = values.get("transaction_reference")
    if reference:
        return session.scalar(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.payment_app == payment_app)
            .where(Transaction.transaction_reference == reference)
        )

    transaction_time = values["transaction_time"]
    assert isinstance(transaction_time, datetime)
    fingerprint = transaction_fingerprint(
        payment_app=payment_app,
        amount=values["amount"],  # type: ignore[arg-type]
        merchant=values.get("merchant"),  # type: ignore[arg-type]
        transaction_time=transaction_time,
        transaction_type=str(values["transaction_type"]),
    )
    # The 10-second fingerprint bucket suppresses notification re-delivery while
    # allowing separate payments made at meaningfully different times.
    return session.scalar(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.fingerprint == fingerprint)
    )


def prepare_fingerprint(values: dict[str, object]) -> str:
    transaction_time = values["transaction_time"]
    assert isinstance(transaction_time, datetime)
    return transaction_fingerprint(
        payment_app=str(values["payment_app"]),
        amount=values["amount"],  # type: ignore[arg-type]
        merchant=values.get("merchant"),  # type: ignore[arg-type]
        transaction_time=transaction_time,
        transaction_type=str(values["transaction_type"]),
    )
