"""Sync tasks for fetching issues from GitHub.

Can be run standalone via: python -m scripts.sync
Or called directly from code: await sync_all()
"""
import asyncio
import logging

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import Company
from app.services.github_client import GitHubGraphQLClient
from app.services.scraper import GitHubScraper

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 2  # seconds between companies


async def sync_all():
    """Sync all companies with error isolation and rate limiting."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company))
        companies = result.scalars().all()

        client = GitHubGraphQLClient()
        scraper = GitHubScraper(session, client)

        logger.info(f"Starting sync for {len(companies)} companies")

        for company in companies:
            try:
                stats = await scraper.scrape_company(company)
                logger.info(f"Synced {company.name}: {stats}")
                await asyncio.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.error(f"Failed to sync {company.name}: {e}")
                continue  # Don't break on individual failures

        logger.info("Sync complete")


async def sync_single(company_id: int):
    """Sync a single company by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        if not company:
            logger.error(f"Company with id {company_id} not found")
            return

        client = GitHubGraphQLClient()
        scraper = GitHubScraper(session, client)

        try:
            stats = await scraper.scrape_company(company)
            logger.info(f"Synced {company.name}: {stats}")
        except Exception as e:
            logger.error(f"Failed to sync {company.name}: {e}")
