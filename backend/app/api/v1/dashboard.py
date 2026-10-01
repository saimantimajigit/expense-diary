from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.dependencies import get_session
from app.schemas.dashboard import DashboardSummary, MonthlyDashboard
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    session: Annotated[Session, Depends(get_session)],
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> DashboardSummary:
    try:
        return dashboard_service.summary(
            session,
            month=month,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/monthly", response_model=MonthlyDashboard)
def get_monthly(
    session: Annotated[Session, Depends(get_session)],
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
) -> MonthlyDashboard:
    try:
        return dashboard_service.monthly(session, month)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
