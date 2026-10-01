from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_session
from app.repositories.category_repository import list_active
from app.schemas.category import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def get_categories(session: Session = Depends(get_session)) -> list[CategoryRead]:
    return [CategoryRead.model_validate(category) for category in list_active(session)]
