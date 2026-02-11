from pydantic import BaseModel, Field


class CreateCompanyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    github_org: str = Field(..., min_length=1, max_length=255)
    website: str | None = None
    description: str | None = None


class UpdateCompanyRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    website: str | None = None
    description: str | None = None
    logo_url: str | None = None
