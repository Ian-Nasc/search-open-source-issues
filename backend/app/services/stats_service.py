from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.issue import Issue
from app.models.repository import Repository
from app.schemas.stats import LabelStat, LanguageStat, StatsResponse


class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self) -> StatsResponse:
        total_issues = await self._count(
            select(func.count(Issue.id)).where(Issue.state == "OPEN")
        )
        total_repositories = await self._count(
            select(func.count(Repository.id))
        )
        total_companies = await self._count(
            select(func.count(Company.id))
        )

        languages = await self._get_language_stats()
        top_labels = await self._get_label_stats()

        last_scraped = await self.session.execute(
            select(func.max(Issue.updated_at))
        )
        last_scraped_at = last_scraped.scalar()

        return StatsResponse(
            total_issues=total_issues,
            total_repositories=total_repositories,
            total_companies=total_companies,
            languages=languages,
            top_labels=top_labels,
            last_scraped_at=last_scraped_at,
        )

    async def _count(self, query) -> int:
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_language_stats(self) -> list[LanguageStat]:
        query = (
            select(
                Repository.primary_language,
                func.count(Issue.id).label("issue_count"),
            )
            .join(Issue, Issue.repository_id == Repository.id)
            .where(Issue.state == "OPEN")
            .where(Repository.primary_language.isnot(None))
            .group_by(Repository.primary_language)
            .order_by(text("issue_count DESC"))
            .limit(20)
        )
        result = await self.session.execute(query)
        return [
            LanguageStat(language=row[0], count=row[1])
            for row in result.all()
        ]

    async def _get_label_stats(self) -> list[LabelStat]:
        query = text("""
            SELECT label, COUNT(*) as label_count
            FROM issues, unnest(labels) AS label
            WHERE state = 'OPEN'
            GROUP BY label
            ORDER BY label_count DESC
            LIMIT 20
        """)
        result = await self.session.execute(query)
        return [
            LabelStat(label=row[0], count=row[1])
            for row in result.all()
        ]
