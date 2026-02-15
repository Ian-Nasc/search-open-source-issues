from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.company import Company
from app.models.suggestion import CompanySuggestion
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse

router = APIRouter()


@router.post("/", response_model=SuggestionResponse, status_code=201)
async def submit_suggestion(
    data: SuggestionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit a company suggestion. No authentication required."""
    # Check if company already exists
    existing_company = await db.execute(
        select(Company).where(Company.github_org == data.github_org)
    )
    if existing_company.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Company with this GitHub org already exists"
        )

    # Check for pending suggestion with same github_org
    existing_suggestion = await db.execute(
        select(CompanySuggestion).where(
            CompanySuggestion.github_org == data.github_org,
            CompanySuggestion.status == "pending",
        )
    )
    if existing_suggestion.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="A suggestion for this GitHub org is already pending"
        )

    suggestion = CompanySuggestion(
        name=data.name,
        github_org=data.github_org,
        email=data.email,
        reason=data.reason,
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    return suggestion
