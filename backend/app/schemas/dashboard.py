from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.transaction import TransactionRead


class CategoryBreakdown(BaseModel):
    category: str
    amount: Decimal
    percentage: Decimal


class DashboardSummary(BaseModel):
    start_date: date
    end_date: date
    total_expense: Decimal
    total_income: Decimal
    total_refund: Decimal
    transaction_count: int
    average_daily_spend: Decimal
    category_breakdown: list[CategoryBreakdown]
    recent_transactions: list[TransactionRead]


class MonthlyDashboard(BaseModel):
    month: str
    total_spent: Decimal
    categories: list[CategoryBreakdown]
