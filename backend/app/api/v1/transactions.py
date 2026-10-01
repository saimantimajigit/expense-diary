from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.dependencies import get_session
from app.schemas.transaction import (
    TransactionCreate,
    TransactionList,
    IngestResult,
    TransactionRead,
    TransactionIngest,
    TransactionUpdate,
)
from app.services import transaction_service
from app.services.categorization_service import InvalidCategoryError
from app.services.transaction_service import TransactionConflictError

router = APIRouter(prefix="/transactions", tags=["transactions"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, session: SessionDep) -> TransactionRead:
    try:
        transaction = transaction_service.create(session, payload)
    except InvalidCategoryError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except TransactionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return TransactionRead.model_validate(transaction)


@router.post("/ingest", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
def ingest_transaction(payload: TransactionIngest, session: SessionDep) -> JSONResponse:
    try:
        transaction, duplicate = transaction_service.ingest(session, payload)
    except InvalidCategoryError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    result = IngestResult(transaction=TransactionRead.model_validate(transaction), duplicate=duplicate)
    return JSONResponse(
        status_code=status.HTTP_200_OK if duplicate else status.HTTP_201_CREATED,
        content=result.model_dump(mode="json"),
        headers={"X-Duplicate": str(duplicate).lower()},
    )


@router.get("", response_model=TransactionList)
def list_transactions(
    session: SessionDep,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category: str | None = None,
    payment_app: Literal["gpay", "phonepe", "paytm", "other"] | None = None,
    merchant: str | None = Query(default=None, max_length=200),
    transaction_type: Literal["expense", "income", "refund"] | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TransactionList:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")
    items, total = transaction_service.list_transactions(
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
    return TransactionList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, session: SessionDep) -> TransactionRead:
    transaction = transaction_service.get(session, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    session: SessionDep,
) -> TransactionRead:
    try:
        transaction = transaction_service.update(session, transaction_id, payload)
    except InvalidCategoryError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, session: SessionDep) -> Response:
    if not transaction_service.delete(session, transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
