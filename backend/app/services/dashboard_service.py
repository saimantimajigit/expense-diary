from calendar import monthrange
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.repositories import dashboard_repository, transaction_repository
from app.schemas.dashboard import CategoryBreakdown, DashboardSummary, MonthlyDashboard

LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")
CENT = Decimal("0.01")


def date_window(
    *,
    month: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime, str]:
    if month and (start_date or end_date):
        raise ValueError("Use either month or a date range")
    if month:
        try:
            first_day = date.fromisoformat(f"{month}-01")
        except ValueError as error:
            raise ValueError("month must use YYYY-MM format") from error
        if first_day.strftime("%Y-%m") != month:
            raise ValueError("month must use YYYY-MM format")
        last_day = date(first_day.year, first_day.month, monthrange(first_day.year, first_day.month)[1])
        start = datetime.combine(first_day, time.min, LOCAL_TIMEZONE)
        end = datetime.combine(last_day + timedelta(days=1), time.min, LOCAL_TIMEZONE)
        return start, end, month

    if start_date is not None or end_date is not None:
        if start_date is None or end_date is None:
            raise ValueError("Both start_date and end_date are required")
        if start_date.tzinfo is None or end_date.tzinfo is None:
            raise ValueError("Date range values must include a timezone")
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")
        return start_date, end_date, f"{start_date.date().isoformat()} to {end_date.date().isoformat()}"

    today = datetime.now(LOCAL_TIMEZONE).date()
    current_month = today.strftime("%Y-%m")
    return date_window(month=current_month, start_date=None, end_date=None)


def build_breakdown(rows: list[tuple[str, Decimal]], total: Decimal) -> list[CategoryBreakdown]:
    if total == 0:
        return [CategoryBreakdown(category=name, amount=amount, percentage=Decimal("0.00")) for name, amount in rows]
    return [
        CategoryBreakdown(
            category=name,
            amount=amount,
            percentage=(amount * Decimal("100") / total).quantize(CENT, rounding=ROUND_HALF_UP),
        )
        for name, amount in rows
    ]


def summary(
    session: Session,
    *,
    month: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> DashboardSummary:
    start, end, _ = date_window(month=month, start_date=start_date, end_date=end_date)
    amounts, count = dashboard_repository.totals(session, start, end)
    expense = amounts["expense"]
    days = max(1, (end.date() - start.date()).days)
    if month is not None:
        today = datetime.now(LOCAL_TIMEZONE).date()
        if start.date() <= today < end.date():
            days = max(1, (today - start.date()).days + 1)
    if month is not None:
        today = datetime.now(LOCAL_TIMEZONE).date()
        if start.date() <= today < end.date():
            days = max(1, (today - start.date()).days + 1)
    average = (expense / Decimal(days)).quantize(CENT, rounding=ROUND_HALF_UP)
    breakdown = build_breakdown(dashboard_repository.categories(session, start, end), expense)
    recent, _ = transaction_repository.list_transactions(
        session,
        start_date=start,
        end_date=end - timedelta(microseconds=1),
        category=None,
        payment_app=None,
        merchant=None,
        transaction_type=None,
        limit=10,
        offset=0,
    )
    return DashboardSummary(
        start_date=start.date(),
        end_date=(end - timedelta(days=1)).date(),
        total_expense=expense,
        total_income=amounts["income"],
        total_refund=amounts["refund"],
        transaction_count=count,
        average_daily_spend=average,
        category_breakdown=breakdown,
        recent_transactions=recent,
    )


def monthly(session: Session, month: str) -> MonthlyDashboard:
    start, end, normalized_month = date_window(month=month, start_date=None, end_date=None)
    amounts, _ = dashboard_repository.totals(session, start, end)
    expense = amounts["expense"]
    return MonthlyDashboard(
        month=normalized_month,
        total_spent=expense,
        categories=build_breakdown(dashboard_repository.categories(session, start, end), expense),
    )
