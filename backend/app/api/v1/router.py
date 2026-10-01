from fastapi import APIRouter

from app.api.v1.categories import router as categories_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.merchant_rules import router as merchant_rules_router
from app.api.v1.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(categories_router)
api_router.include_router(dashboard_router)
api_router.include_router(merchant_rules_router)
api_router.include_router(transactions_router)
