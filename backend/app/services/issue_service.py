import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.issue import Issue
from app.models.repository import Repository
from app.schemas.issue import (
    CompanyBrief,
    IssueListResponse,
    IssueResponse,
    LabelDetail,
    RepositoryBrief,
)


class IssueService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_issues(
        self,
        page: int = 1,
        page_size: int = 20,
        languages: list[str] | None = None,
        companies: list[str] | None = None,
        labels: list[str] | None = None,
        min_stars: int | None = None,
        sort_by: str = "updated",
        sort_order: str = "desc",
    ) -> IssueListResponse:
        base_query = (
            select(Issue)
            .join(Repository, Issue.repository_id == Repository.id)
            .join(Company, Repository.company_id == Company.id)
            .where(Issue.state == "OPEN")
        )

        if languages:
            base_query = base_query.where(
                Repository.primary_language.in_(languages)
            )
        if companies:
            base_query = base_query.where(Company.slug.in_(companies))
        if labels:
            base_query = base_query.where(Issue.labels.overlap(labels))
        if min_stars:
            base_query = base_query.where(Repository.stars >= min_stars)

        sort_column = {
            "updated": Issue.github_updated_at,
            "created": Issue.github_created_at,
            "stars": Repository.stars,
        }.get(sort_by, Issue.github_updated_at)

        if sort_order == "asc":
            base_query = base_query.order_by(sort_column.asc().nullslast())
        else:
            base_query = base_query.order_by(sort_column.desc().nullsfirst())

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            base_query.options(
                selectinload(Issue.repository).selectinload(Repository.company)
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(query)
        issues = result.scalars().all()

        return IssueListResponse(
            items=[self._to_response(issue) for issue in issues],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    async def get_issue(self, issue_id: int) -> IssueResponse | None:
        query = (
            select(Issue)
            .options(
                selectinload(Issue.repository).selectinload(Repository.company)
            )
            .where(Issue.id == issue_id)
        )
        result = await self.session.execute(query)
        issue = result.scalar_one_or_none()
        if not issue:
            return None
        return self._to_response(issue)

    def _to_response(self, issue: Issue) -> IssueResponse:
        repo = issue.repository
        company = repo.company

        label_details = None
        if issue.label_details:
            label_details = [LabelDetail(**ld) for ld in issue.label_details]

        return IssueResponse(
            id=issue.id,
            github_id=issue.github_id,
            number=issue.number,
            title=issue.title,
            url=issue.url,
            state=issue.state,
            labels=issue.labels,
            label_details=label_details,
            comment_count=issue.comment_count,
            github_created_at=issue.github_created_at,
            github_updated_at=issue.github_updated_at,
            repository=RepositoryBrief(
                id=repo.id,
                name=repo.name,
                full_name=repo.full_name,
                primary_language=repo.primary_language,
                stars=repo.stars,
                url=repo.url,
            ),
            company=CompanyBrief(
                id=company.id,
                name=company.name,
                slug=company.slug,
                logo_url=company.logo_url,
            ),
        )
