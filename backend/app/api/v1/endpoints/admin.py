import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.company import Company
from app.models.issue import Issue
from app.models.repository import Repository
from app.schemas.admin import CreateCompanyRequest, UpdateCompanyRequest
from app.schemas.company import CompanyResponse
from app.tasks.scraping import scrape_single_company

router = APIRouter()


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/companies/", response_model=CompanyResponse, status_code=201)
async def create_company(
    data: CreateCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Company).where(Company.github_org == data.github_org)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Company with this GitHub org already exists"
        )

    slug = slugify(data.name)
    logo_url = f"https://avatars.githubusercontent.com/{data.github_org}"

    company = Company(
        name=data.name,
        slug=slug,
        github_org=data.github_org,
        logo_url=logo_url,
        website=data.website,
        description=data.description,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    scrape_single_company.delay(company.id)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        logo_url=company.logo_url,
        website=company.website,
        description=company.description,
        github_org=company.github_org,
        repository_count=0,
        issue_count=0,
    )


@router.put("/companies/{slug}", response_model=CompanyResponse)
async def update_company(
    slug: str,
    data: UpdateCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.slug == slug))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        logo_url=company.logo_url,
        website=company.website,
        description=company.description,
        github_org=company.github_org,
    )


@router.delete("/companies/{slug}", status_code=204)
async def delete_company(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.slug == slug))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    repo_ids_result = await db.execute(
        select(Repository.id).where(Repository.company_id == company.id)
    )
    repo_ids = [r[0] for r in repo_ids_result.all()]

    if repo_ids:
        await db.execute(
            delete(Issue).where(Issue.repository_id.in_(repo_ids))
        )
        await db.execute(
            delete(Repository).where(Repository.company_id == company.id)
        )

    await db.execute(delete(Company).where(Company.id == company.id))
    await db.commit()
