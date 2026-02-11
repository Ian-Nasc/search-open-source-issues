import asyncio
import logging

from sqlalchemy import select

from app.celery_app import celery
from app.core.database import AsyncSessionLocal
from app.models import Company
from app.services.github_client import GitHubGraphQLClient
from app.services.scraper import GitHubScraper

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_all_companies(self):
    asyncio.run(_scrape_all())


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_single_company(self, company_id: int):
    asyncio.run(_scrape_single(company_id))


async def _scrape_all():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company))
        companies = result.scalars().all()

        client = GitHubGraphQLClient()
        scraper = GitHubScraper(session, client)

        for company in companies:
            try:
                stats = await scraper.scrape_company(company)
                logger.info(f"Scraped {company.name}: {stats}")
            except Exception as e:
                logger.error(f"Error scraping {company.name}: {e}")
                continue


async def _scrape_single(company_id: int):
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
            logger.info(f"Scraped {company.name}: {stats}")
        except Exception as e:
            logger.error(f"Error scraping {company.name}: {e}")
