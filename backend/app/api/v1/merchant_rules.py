from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_session
from app.schemas.merchant_rule import MerchantRuleCreate, MerchantRuleRead
from app.services import merchant_rule_service
from app.services.categorization_service import InvalidCategoryError

router = APIRouter(prefix="/merchant-rules", tags=["merchant-rules"])


@router.get("", response_model=list[MerchantRuleRead])
def list_merchant_rules(session: Annotated[Session, Depends(get_session)]) -> list[MerchantRuleRead]:
    return [MerchantRuleRead.model_validate(rule) for rule in merchant_rule_service.list_rules(session)]


@router.post("", response_model=MerchantRuleRead, status_code=status.HTTP_201_CREATED)
def learn_merchant_rule(
    payload: MerchantRuleCreate,
    session: Annotated[Session, Depends(get_session)],
) -> MerchantRuleRead:
    try:
        rule = merchant_rule_service.create_or_update(session, payload)
    except InvalidCategoryError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return MerchantRuleRead.model_validate(rule)
