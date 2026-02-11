from datetime import datetime

from pydantic import BaseModel


class LabelDetail(BaseModel):
    name: str
    color: str
    description: str | None = None


class CompanyBrief(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None

    class Config:
        from_attributes = True


class RepositoryBrief(BaseModel):
    id: int
    name: str
    full_name: str
    primary_language: str | None
    stars: int
    url: str

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    id: int
    github_id: int
    number: int
    title: str
    url: str
    state: str
    labels: list[str] | None
    label_details: list[LabelDetail] | None
    comment_count: int
    github_created_at: datetime | None
    github_updated_at: datetime | None
    repository: RepositoryBrief
    company: CompanyBrief

    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    items: list[IssueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
