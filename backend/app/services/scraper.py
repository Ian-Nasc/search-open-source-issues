import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.company import Company
from app.models.issue import Issue
from app.models.repository import Repository
from app.services.github_client import GitHubGraphQLClient

logger = logging.getLogger(__name__)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubScraper:
    def __init__(self, session: AsyncSession, github_client: GitHubGraphQLClient):
        self.session = session
        self.github_client = github_client

    async def scrape_company(self, company: Company) -> dict:
        stats = {"repos": 0, "issues_created": 0, "issues_updated": 0}

        repos = await self.github_client.fetch_all_org_repositories(company.github_org)
        stats["repos"] = len(repos)

        for repo_data in repos:
            repo = await self._upsert_repository(repo_data, company.id)

            issues = await self.github_client.fetch_all_repo_issues(
                company.github_org,
                repo_data["name"],
                max_issues=settings.ISSUES_PER_REPO,
            )

            issue_stats = await self._upsert_issues(issues, repo.id)
            stats["issues_created"] += issue_stats["created"]
            stats["issues_updated"] += issue_stats["updated"]

            active_github_ids = {i["databaseId"] for i in issues}
            await self._mark_stale_issues_closed(repo.id, active_github_ids)

        await self.session.commit()
        return stats

    async def _upsert_repository(
        self, data: dict, company_id: int
    ) -> Repository:
        topics = [
            node["topic"]["name"]
            for node in data.get("repositoryTopics", {}).get("nodes", [])
        ]
        primary_language = None
        if data.get("primaryLanguage"):
            primary_language = data["primaryLanguage"]["name"]

        values = {
            "github_id": data["databaseId"],
            "name": data["name"],
            "full_name": data["nameWithOwner"],
            "description": data.get("description"),
            "url": data["url"],
            "primary_language": primary_language,
            "stars": data["stargazerCount"],
            "forks": data["forkCount"],
            "topics": topics or None,
            "company_id": company_id,
        }

        stmt = (
            insert(Repository)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["github_id"],
                set_={
                    "name": values["name"],
                    "full_name": values["full_name"],
                    "description": values["description"],
                    "url": values["url"],
                    "primary_language": values["primary_language"],
                    "stars": values["stars"],
                    "forks": values["forks"],
                    "topics": values["topics"],
                },
            )
            .returning(Repository)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _upsert_issues(self, issues: list[dict], repo_id: int) -> dict:
        stats = {"created": 0, "updated": 0}

        for issue_data in issues:
            labels = [
                node["name"]
                for node in issue_data.get("labels", {}).get("nodes", [])
            ]
            label_details = [
                {
                    "name": node["name"],
                    "color": node["color"],
                    "description": node.get("description"),
                }
                for node in issue_data.get("labels", {}).get("nodes", [])
            ]

            values = {
                "github_id": issue_data["databaseId"],
                "number": issue_data["number"],
                "title": issue_data["title"],
                "body": issue_data.get("body"),
                "url": issue_data["url"],
                "state": issue_data["state"],
                "labels": labels or None,
                "label_details": label_details or None,
                "comment_count": issue_data.get("comments", {}).get(
                    "totalCount", 0
                ),
                "github_created_at": _parse_dt(issue_data.get("createdAt")),
                "github_updated_at": _parse_dt(issue_data.get("updatedAt")),
                "repository_id": repo_id,
            }

            stmt = (
                insert(Issue)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["github_id"],
                    set_={
                        "title": values["title"],
                        "body": values["body"],
                        "state": values["state"],
                        "labels": values["labels"],
                        "label_details": values["label_details"],
                        "comment_count": values["comment_count"],
                        "github_updated_at": values["github_updated_at"],
                    },
                )
            )
            await self.session.execute(stmt)
            stats["updated"] += 1

        return stats

    async def _mark_stale_issues_closed(
        self, repo_id: int, active_github_ids: set[int]
    ):
        if not active_github_ids:
            return

        stmt = (
            update(Issue)
            .where(
                Issue.repository_id == repo_id,
                Issue.state == "OPEN",
                Issue.github_id.notin_(active_github_ids),
            )
            .values(state="CLOSED")
        )
        await self.session.execute(stmt)
