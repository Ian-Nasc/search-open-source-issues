from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.issue import IssueListResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.get("/", response_model=IssueListResponse)
async def search_issues(
    q: str = Query(..., min_length=2, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: list[str] | None = Query(None),
    company: list[str] | None = Query(None),
    label: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    return await service.hybrid_search(
        query=q,
        page=page,
        page_size=page_size,
        languages=language,
        companies=company,
        labels=label,
    )
