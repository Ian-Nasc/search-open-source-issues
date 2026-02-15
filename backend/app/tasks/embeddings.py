"""Embedding generation tasks.

Can be run standalone via: python -m scripts.generate_embeddings
Or called directly from code: await generate_missing_embeddings()
"""
import logging

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models import Issue
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


async def generate_missing_embeddings():
    """Generate embeddings for issues that don't have them yet."""
    embedding_service = EmbeddingService()

    async with AsyncSessionLocal() as session:
        total_processed = 0

        while True:
            result = await session.execute(
                select(Issue)
                .where(Issue.embedding.is_(None))
                .where(Issue.state == "OPEN")
                .limit(BATCH_SIZE)
            )
            issues = result.scalars().all()

            if not issues:
                logger.info(f"Done. Total issues processed: {total_processed}")
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
            total_processed += len(issues)
            logger.info(f"Generated embeddings for {len(issues)} issues (total: {total_processed})")
