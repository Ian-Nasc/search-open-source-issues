import asyncio
import logging

from sqlalchemy import select, update

from app.celery_app import celery
from app.core.database import AsyncSessionLocal
from app.models import Issue
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_missing_embeddings(self):
    asyncio.run(_generate_embeddings())


async def _generate_embeddings():
    embedding_service = EmbeddingService()

    async with AsyncSessionLocal() as session:
        while True:
            result = await session.execute(
                select(Issue)
                .where(Issue.embedding.is_(None))
                .where(Issue.state == "OPEN")
                .limit(BATCH_SIZE)
            )
            issues = result.scalars().all()

            if not issues:
                logger.info("No more issues without embeddings")
                break

            texts = []
            for issue in issues:
                body_snippet = (issue.body or "")[:500]
                text = f"{issue.title} {body_snippet}".strip()
                texts.append(text)

            try:
                embeddings = await embedding_service.generate_embeddings_batch(texts)
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                break

            for issue, embedding in zip(issues, embeddings):
                await session.execute(
                    update(Issue)
                    .where(Issue.id == issue.id)
                    .values(embedding=embedding)
                )

            await session.commit()
            logger.info(f"Generated embeddings for {len(issues)} issues")
