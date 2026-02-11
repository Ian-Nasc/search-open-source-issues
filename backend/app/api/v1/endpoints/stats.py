from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stats import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    service = StatsService(db)
    return await service.get_stats()
