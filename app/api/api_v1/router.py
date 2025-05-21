# File: backend/app/api/api_v1/router.py
# Status: COMPLETE
# Dependencies: fastapi
from fastapi import APIRouter

# Import router modules directly
from app.api.api_v1.endpoints.auth import router as auth_router
from app.api.api_v1.endpoints.users import router as users_router 
from app.api.api_v1.endpoints.properties import router as properties_router
from app.api.api_v1.endpoints.tokens import router as tokens_router
from app.api.api_v1.endpoints.messages import router as messages_router
from app.api.api_v1.endpoints.payments import router as payments_router
from app.api.api_v1.endpoints.subscriptions import router as subscriptions_router
from app.api.api_v1.endpoints.verifications import router as verifications_router
from app.api.api_v1.endpoints.admin import router as admin_router
from app.api.api_v1.endpoints.debug import router as debug_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(tokens_router, prefix="/tokens", tags=["tokens"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(verifications_router, prefix="/verifications", tags=["verifications"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(debug_router, prefix="/debug", tags=["debug"])