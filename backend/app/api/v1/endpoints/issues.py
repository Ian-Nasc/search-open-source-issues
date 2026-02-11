from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.issue import IssueListResponse, IssueResponse
from app.services.issue_service import IssueService

router = APIRouter()


@router.get("/", response_model=IssueListResponse)
async def list_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: list[str] | None = Query(None),
    company: list[str] | None = Query(None),
    label: list[str] | None = Query(None),
    min_stars: int | None = Query(None),
    sort_by: str = Query("updated", pattern="^(updated|created|stars)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    service = IssueService(db)
    return await service.list_issues(
        page=page,
        page_size=page_size,
        languages=language,
        companies=company,
        labels=label,
        min_stars=min_stars,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = IssueService(db)
    issue = await service.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue
