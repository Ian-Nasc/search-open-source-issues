from datetime import datetime

from pydantic import BaseModel


class LanguageStat(BaseModel):
    language: str
    count: int


class LabelStat(BaseModel):
    label: str
    count: int


class StatsResponse(BaseModel):
    total_issues: int
    total_repositories: int
    total_companies: int
    languages: list[LanguageStat]
    top_labels: list[LabelStat]
    last_scraped_at: datetime | None
