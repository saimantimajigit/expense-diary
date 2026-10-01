from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
TransactionType = Literal["expense", "income", "refund"]
TransactionSource = Literal["notification", "manual", "statement_import"]
PaymentApp = Literal["gpay", "phonepe", "paytm", "other"]


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Money
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "INR"
    transaction_type: TransactionType = "expense"
    merchant: Annotated[str | None, Field(max_length=200)] = None
    description: Annotated[str | None, Field(max_length=500)] = None
    category_id: int | None = None
    source: TransactionSource = "manual"
    payment_app: PaymentApp = "other"
    transaction_reference: Annotated[str | None, Field(max_length=160)] = None
    transaction_time: datetime
    raw_notification: Annotated[str | None, Field(max_length=4000)] = None
    raw_payload: dict[str, object] | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized.isalpha():
            raise ValueError("currency must use a three-letter code")
        return normalized

    @field_validator("transaction_reference")
    @classmethod
    def normalize_reference(cls, value: str | None) -> str | None:
        normalized = value.strip() if value is not None else None
        return normalized or None

    @field_validator("transaction_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("transaction_time must include a timezone")
        return value


class TransactionIngest(TransactionCreate):
    source: Literal["notification"] = "notification"
    payment_app: PaymentApp


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Money | None = None
    currency: Annotated[str, Field(min_length=3, max_length=3)] | None = None
    transaction_type: TransactionType | None = None
    merchant: Annotated[str, Field(max_length=200)] | None = None
    description: Annotated[str, Field(max_length=500)] | None = None
    category_id: int | None = None
    transaction_time: datetime | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.upper()
        if not normalized.isalpha():
            raise ValueError("currency must use a three-letter code")
        return normalized

    @field_validator("transaction_time")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("transaction_time must include a timezone")
        return value


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    currency: str
    transaction_type: str
    merchant: str | None
    description: str | None
    category_id: int | None
    category: CategorySummary | None
    source: str
    payment_app: str
    transaction_reference: str | None
    transaction_time: datetime
    created_at: datetime
    updated_at: datetime


class IngestResult(BaseModel):
    transaction: TransactionRead
    duplicate: bool


class TransactionList(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int
