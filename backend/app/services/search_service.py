import math

from sqlalchemy import case, func, or_, select, text
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
from app.services.embedding_service import EmbeddingService


class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = EmbeddingService()

    async def hybrid_search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        languages: list[str] | None = None,
        companies: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> IssueListResponse:
        query_embedding = await self.embedding_service.generate_embedding(query)

        cosine_distance = Issue.embedding.cosine_distance(query_embedding)
        semantic_score = (1 - cosine_distance).label("semantic_score")

        keyword_score = case(
            (Issue.title.ilike(f"%{query}%"), 1.0),
            else_=0.0,
        ).label("keyword_score")

        combined_score = (
            0.6 * (1 - cosine_distance) + 0.4 * keyword_score
        ).label("combined_score")

        base_query = (
            select(Issue, combined_score)
            .join(Repository, Issue.repository_id == Repository.id)
            .join(Company, Repository.company_id == Company.id)
            .where(Issue.state == "OPEN")
            .where(
                or_(
                    Issue.embedding.isnot(None),
                    Issue.title.ilike(f"%{query}%"),
                )
            )
        )

        if languages:
            base_query = base_query.where(
                Repository.primary_language.in_(languages)
            )
        if companies:
            base_query = base_query.where(Company.slug.in_(companies))
        if labels:
            base_query = base_query.where(Issue.labels.overlap(labels))

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query_stmt = (
            base_query.options(
                selectinload(Issue.repository).selectinload(Repository.company)
            )
            .order_by(text("combined_score DESC"))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query_stmt)
        rows = result.all()

        items = []
        for row in rows:
            issue = row[0]
            items.append(self._to_response(issue))

        return IssueListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )

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
