from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None
    website: str | None
    description: str | None
    github_org: str
    repository_count: int = 0
    issue_count: int = 0

    class Config:
        from_attributes = True
