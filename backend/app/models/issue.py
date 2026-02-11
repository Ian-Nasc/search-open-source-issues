from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class Issue(TimestampMixin, Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512))
    state: Mapped[str] = mapped_column(String(20), index=True)
    labels: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    label_details: Mapped[dict | None] = mapped_column(JSONB)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    github_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    github_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    repository: Mapped[Repository] = relationship(back_populates="issues")

    __table_args__ = (
        Index(
            "ix_issues_embedding_cosine",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
