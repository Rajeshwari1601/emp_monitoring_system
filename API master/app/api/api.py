from fastapi import APIRouter
from app.api.v1.endpoints import auth, client, admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(client.router, prefix="/client", tags=["client"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
