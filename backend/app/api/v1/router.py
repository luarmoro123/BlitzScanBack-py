
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, scan

api_router = APIRouter()
api_router.include_router(auth.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])

