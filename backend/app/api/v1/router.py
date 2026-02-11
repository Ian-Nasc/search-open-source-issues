from fastapi import APIRouter

from app.api.v1.endpoints import admin, companies, issues, search, stats

api_router = APIRouter()
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
