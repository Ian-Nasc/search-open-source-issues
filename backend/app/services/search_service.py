"""Search service with tiered filtering and caching.

Tier 1: Cache hit → instant, R$0
Tier 2: Simple keyword search → SQL LIKE, R$0
Tier 3: Full semantic search → OpenAI embedding
"""
import logging
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
from app.services.search_cache import search_cache

logger = logging.getLogger(__name__)

# Known programming keywords that can use simple keyword search
KNOWN_KEYWORDS = {
    "python", "javascript", "typescript", "react", "rust", "go", "golang",
    "java", "kotlin", "swift", "ruby", "php", "c++", "cpp", "c#", "csharp",
    "node", "nodejs", "vue", "angular", "svelte", "nextjs", "django", "flask",
    "fastapi", "rails", "spring", "docker", "kubernetes", "k8s", "aws", "gcp",
    "azure", "terraform", "ansible", "linux", "postgres", "mysql", "mongodb",
    "redis", "graphql", "rest", "api", "frontend", "backend", "fullstack",
    "devops", "cicd", "testing", "documentation", "docs", "bug", "feature",
    "enhancement", "refactor", "performance", "security", "accessibility",
}


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
        # Build filter dict for cache key
        cache_filters = {}
        if languages:
            cache_filters["languages"] = sorted(languages)
        if companies:
            cache_filters["companies"] = sorted(companies)
        if labels:
            cache_filters["labels"] = sorted(labels)

        # TIER 1: Check cache first (R$0)
        cached_ids = search_cache.get(query, cache_filters)
        if cached_ids is not None:
            logger.info(f"Cache hit for '{query}' ({len(cached_ids)} results)")
            return await self._fetch_issues_by_ids(cached_ids, page, page_size)

        # TIER 2: Simple keyword search for short/common queries (R$0)
        if self._is_simple_keyword(query):
            logger.info(f"Using keyword search for '{query}'")
            result = await self._keyword_search(
                query, page, page_size, languages, companies, labels
            )
            # Cache the IDs
            all_ids = await self._get_all_matching_ids_keyword(
                query, languages, companies, labels
            )
            search_cache.set(query, cache_filters, all_ids)
            return result

        # TIER 3: Full semantic search (uses OpenAI embedding)
        logger.info(f"Using semantic search for '{query}'")
        result = await self._semantic_search(
            query, page, page_size, languages, companies, labels
        )
        # Cache the IDs
        all_ids = await self._get_all_matching_ids_semantic(
            query, languages, companies, labels
        )
        search_cache.set(query, cache_filters, all_ids)
        return result

    def _is_simple_keyword(self, query: str) -> bool:
        """Check if query is a simple keyword that doesn't need semantic search."""
        words = query.lower().strip().split()
        # Single word or two words that are known keywords
        if len(words) <= 2:
            return all(w in KNOWN_KEYWORDS for w in words)
        return False

    async def _keyword_search(
        self,
        query: str,
        page: int,
        page_size: int,
        languages: list[str] | None,
        companies: list[str] | None,
        labels: list[str] | None,
    ) -> IssueListResponse:
        """Simple keyword-based search using SQL LIKE."""
        base_query = (
            select(Issue)
            .join(Repository, Issue.repository_id == Repository.id)
            .join(Company, Repository.company_id == Company.id)
            .where(Issue.state == "OPEN")
            .where(
                or_(
                    Issue.title.ilike(f"%{query}%"),
                    Issue.body.ilike(f"%{query}%"),
                )
            )
        )

        base_query = self._apply_filters(base_query, languages, companies, labels)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Fetch page
        query_stmt = (
            base_query.options(
                selectinload(Issue.repository).selectinload(Repository.company)
            )
            .order_by(Issue.github_updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query_stmt)
        issues = result.scalars().all()

        return IssueListResponse(
            items=[self._to_response(issue) for issue in issues],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    async def _semantic_search(
        self,
        query: str,
        page: int,
        page_size: int,
        languages: list[str] | None,
        companies: list[str] | None,
        labels: list[str] | None,
    ) -> IssueListResponse:
        """Semantic search using embeddings."""
        query_embedding = await self.embedding_service.generate_embedding(query)

        cosine_distance = Issue.embedding.cosine_distance(query_embedding)

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

        base_query = self._apply_filters(base_query, languages, companies, labels)

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

    def _apply_filters(self, query, languages, companies, labels):
        """Apply common filters to a query."""
        if languages:
            query = query.where(Repository.primary_language.in_(languages))
        if companies:
            query = query.where(Company.slug.in_(companies))
        if labels:
            query = query.where(Issue.labels.overlap(labels))
        return query

    async def _fetch_issues_by_ids(
        self, issue_ids: list[int], page: int, page_size: int
    ) -> IssueListResponse:
        """Fetch issues by IDs (for cache hits)."""
        if not issue_ids:
            return IssueListResponse(
                items=[], total=0, page=page, page_size=page_size, total_pages=0
            )

        total = len(issue_ids)
        start = (page - 1) * page_size
        end = start + page_size
        page_ids = issue_ids[start:end]

        if not page_ids:
            return IssueListResponse(
                items=[], total=total, page=page, page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

        query = (
            select(Issue)
            .where(Issue.id.in_(page_ids))
            .options(
                selectinload(Issue.repository).selectinload(Repository.company)
            )
        )
        result = await self.session.execute(query)
        issues = result.scalars().all()

        # Preserve order from cached IDs
        issue_map = {i.id: i for i in issues}
        ordered_issues = [issue_map[id] for id in page_ids if id in issue_map]

        return IssueListResponse(
            items=[self._to_response(issue) for issue in ordered_issues],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )

    async def _get_all_matching_ids_keyword(
        self,
        query: str,
        languages: list[str] | None,
        companies: list[str] | None,
        labels: list[str] | None,
    ) -> list[int]:
        """Get all matching issue IDs for keyword search (for caching)."""
        base_query = (
            select(Issue.id)
            .join(Repository, Issue.repository_id == Repository.id)
            .join(Company, Repository.company_id == Company.id)
            .where(Issue.state == "OPEN")
            .where(
                or_(
                    Issue.title.ilike(f"%{query}%"),
                    Issue.body.ilike(f"%{query}%"),
                )
            )
            .order_by(Issue.github_updated_at.desc())
            .limit(1000)  # Cap cached results
        )
        base_query = self._apply_filters(base_query, languages, companies, labels)
        result = await self.session.execute(base_query)
        return [row[0] for row in result.all()]

    async def _get_all_matching_ids_semantic(
        self,
        query: str,
        languages: list[str] | None,
        companies: list[str] | None,
        labels: list[str] | None,
    ) -> list[int]:
        """Get all matching issue IDs for semantic search (for caching)."""
        query_embedding = await self.embedding_service.generate_embedding(query)
        cosine_distance = Issue.embedding.cosine_distance(query_embedding)

        keyword_score = case(
            (Issue.title.ilike(f"%{query}%"), 1.0),
            else_=0.0,
        )
        combined_score = (0.6 * (1 - cosine_distance) + 0.4 * keyword_score)

        base_query = (
            select(Issue.id, combined_score.label("score"))
            .join(Repository, Issue.repository_id == Repository.id)
            .join(Company, Repository.company_id == Company.id)
            .where(Issue.state == "OPEN")
            .where(
                or_(
                    Issue.embedding.isnot(None),
                    Issue.title.ilike(f"%{query}%"),
                )
            )
            .order_by(text("score DESC"))
            .limit(1000)  # Cap cached results
        )
        base_query = self._apply_filters(base_query, languages, companies, labels)
        result = await self.session.execute(base_query)
        return [row[0] for row in result.all()]

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
