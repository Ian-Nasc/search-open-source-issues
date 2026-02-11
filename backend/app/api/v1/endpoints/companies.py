from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.company import Company
from app.models.issue import Issue
from app.models.repository import Repository
from app.schemas.company import CompanyResponse

router = APIRouter()


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Company,
            func.count(func.distinct(Repository.id)).label("repository_count"),
            func.count(
                func.distinct(
                    func.case((Issue.state == "OPEN", Issue.id))
                )
            ).label("issue_count"),
        )
        .outerjoin(Repository, Repository.company_id == Company.id)
        .outerjoin(Issue, Issue.repository_id == Repository.id)
        .group_by(Company.id)
        .order_by(Company.name)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        CompanyResponse(
            id=row[0].id,
            name=row[0].name,
            slug=row[0].slug,
            logo_url=row[0].logo_url,
            website=row[0].website,
            description=row[0].description,
            github_org=row[0].github_org,
            repository_count=row[1],
            issue_count=row[2],
        )
        for row in rows
    ]


@router.get("/{slug}", response_model=CompanyResponse)
async def get_company(slug: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Company,
            func.count(func.distinct(Repository.id)).label("repository_count"),
            func.count(
                func.distinct(
                    func.case((Issue.state == "OPEN", Issue.id))
                )
            ).label("issue_count"),
        )
        .outerjoin(Repository, Repository.company_id == Company.id)
        .outerjoin(Issue, Issue.repository_id == Repository.id)
        .where(Company.slug == slug)
        .group_by(Company.id)
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyResponse(
        id=row[0].id,
        name=row[0].name,
        slug=row[0].slug,
        logo_url=row[0].logo_url,
        website=row[0].website,
        description=row[0].description,
        github_org=row[0].github_org,
        repository_count=row[1],
        issue_count=row[2],
    )
