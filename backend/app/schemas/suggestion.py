from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SuggestionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    github_org: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr | None = None
    reason: str | None = Field(None, max_length=1000)


class SuggestionResponse(BaseModel):
    id: int
    name: str
    github_org: str
    email: str | None
    reason: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
