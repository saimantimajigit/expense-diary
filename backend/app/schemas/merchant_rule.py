from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class MerchantRuleCreate(BaseModel):
    merchant_pattern: Annotated[str, Field(min_length=1, max_length=160)]
    category_id: int = Field(gt=0)
    priority: int = Field(default=10, ge=1, le=1000)
    is_active: bool = True


class MerchantRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_pattern: str
    category_id: int
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
