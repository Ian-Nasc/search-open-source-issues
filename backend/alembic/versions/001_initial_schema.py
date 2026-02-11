"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("slug", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("logo_url", sa.String(512)),
        sa.Column("website", sa.String(512)),
        sa.Column("description", sa.Text()),
        sa.Column("github_org", sa.String(255), unique=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("github_id", sa.BigInteger(), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "full_name", sa.String(512), unique=True, nullable=False, index=True
        ),
        sa.Column("description", sa.Text()),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("primary_language", sa.String(100), index=True),
        sa.Column("stars", sa.Integer(), default=0, nullable=False),
        sa.Column("forks", sa.Integer(), default=0, nullable=False),
        sa.Column("topics", postgresql.ARRAY(sa.String())),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("github_id", sa.BigInteger(), unique=True, nullable=False, index=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, index=True),
        sa.Column("labels", postgresql.ARRAY(sa.String())),
        sa.Column("label_details", postgresql.JSONB()),
        sa.Column("comment_count", sa.Integer(), default=0, nullable=False),
        sa.Column("github_created_at", sa.DateTime(timezone=True)),
        sa.Column("github_updated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "repository_id",
            sa.Integer(),
            sa.ForeignKey("repositories.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("embedding", Vector(1536)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_issues_embedding_cosine",
        "issues",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_issues_embedding_cosine", table_name="issues")
    op.drop_table("issues")
    op.drop_table("repositories")
    op.drop_table("companies")
    op.execute("DROP EXTENSION IF EXISTS vector")
