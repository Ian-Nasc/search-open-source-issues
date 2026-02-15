# Backend Development Guide

This document outlines the coding principles, patterns, and conventions for the OSS Issue Finder backend.

---

## Table of Contents

- [Type Safety](#type-safety)
- [Naming Conventions](#naming-conventions)
- [SOLID Principles](#solid-principles)
- [Code Organization](#code-organization)
- [Writing Patterns](#writing-patterns)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Running Quality Checks](#running-quality-checks)

---

## Type Safety

**All code must be fully typed.** We use `mypy` in strict mode and `ruff` with annotation rules.

### Rules

1. **Always annotate function parameters and return types**

```python
# Good
async def get_company_by_slug(slug: str) -> Company | None:
    ...

# Bad - missing return type
async def get_company_by_slug(slug: str):
    ...
```

2. **Use `None` union for nullable returns**

```python
# Good
def find_user(user_id: int) -> User | None:
    ...

# Bad - implicit None return
def find_user(user_id: int) -> User:
    if not found:
        return None  # Type error!
```

3. **Annotate class attributes**

```python
# Good
class GitHubClient:
    base_url: str
    token: str
    _session: httpx.AsyncClient | None

    def __init__(self, token: str) -> None:
        self.token = token
        self._session = None
```

4. **Use generics for collections**

```python
# Good
def process_items(items: list[Issue]) -> dict[str, int]:
    ...

# Bad - untyped collections
def process_items(items: list) -> dict:
    ...
```

5. **Type aliases for complex types**

```python
# Good - clear intent
IssueId = int
LabelMap = dict[str, list[str]]

def categorize_issues(issues: list[Issue]) -> LabelMap:
    ...
```

---

## Naming Conventions

### Variables and Functions

| Type | Convention | Example |
|------|------------|---------|
| Variables | `snake_case` | `issue_count`, `github_token` |
| Functions | `snake_case` | `get_open_issues()`, `sync_company()` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES`, `CACHE_TTL_HOURS` |
| Classes | `PascalCase` | `GitHubClient`, `SearchService` |
| Private | `_leading_underscore` | `_parse_response()`, `_session` |

### Naming Guidelines

1. **Be explicit, not clever**

```python
# Good
def get_issues_by_company(company_id: int) -> list[Issue]:
    ...

# Bad - ambiguous
def fetch(cid: int) -> list:
    ...
```

2. **Use verbs for actions, nouns for data**

```python
# Functions (verbs)
def sync_repositories() -> None: ...
def generate_embedding(text: str) -> list[float]: ...
def calculate_score(issue: Issue) -> float: ...

# Variables (nouns)
repository_count: int
active_companies: list[Company]
search_results: IssueListResponse
```

3. **Boolean names should read as questions**

```python
# Good
is_active: bool
has_embedding: bool
should_retry: bool

# Bad
active: bool  # Unclear if it's a status or action
retry: bool   # Is this a flag or a count?
```

4. **Avoid abbreviations except well-known ones**

```python
# Good
repository, configuration, database
db, api, url, id  # Well-known abbreviations

# Bad
repo, cfg, repo_cnt
```

5. **Collection names should be plural**

```python
# Good
issues: list[Issue]
companies: dict[str, Company]

# Bad
issue_list: list[Issue]  # Redundant "list"
company: dict[str, Company]  # Singular for collection
```

---

## SOLID Principles

### S - Single Responsibility Principle

Each class/module should have one reason to change.

```python
# Good - separate concerns
class GitHubClient:
    """Handles HTTP communication with GitHub API."""
    async def fetch_repositories(self, org: str) -> list[dict]: ...

class GitHubScraper:
    """Orchestrates scraping and data transformation."""
    def __init__(self, client: GitHubClient, session: AsyncSession) -> None: ...
    async def scrape_company(self, company: Company) -> ScrapeStats: ...

# Bad - mixed concerns
class GitHubScraper:
    """Does HTTP, parsing, and database operations."""
    async def fetch_and_save_repos(self, org: str) -> None:
        response = await httpx.get(...)  # HTTP concern
        data = self._parse(response)      # Parsing concern
        await self.session.add(...)       # Database concern
```

### O - Open/Closed Principle

Open for extension, closed for modification.

```python
# Good - extensible via new implementations
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    @abstractmethod
    async def generate(self, text: str) -> list[float]: ...

class OpenAIEmbedding(EmbeddingProvider):
    async def generate(self, text: str) -> list[float]:
        # OpenAI implementation
        ...

class LocalEmbedding(EmbeddingProvider):
    async def generate(self, text: str) -> list[float]:
        # Local model implementation
        ...
```

### L - Liskov Substitution Principle

Subtypes must be substitutable for their base types.

```python
# Good - subtypes honor the contract
class Repository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Model | None: ...

class CompanyRepository(Repository):
    async def get_by_id(self, id: int) -> Company | None:
        # Returns Company (subtype of Model) or None - valid
        ...
```

### I - Interface Segregation Principle

Clients shouldn't depend on interfaces they don't use.

```python
# Good - focused interfaces
class Readable(Protocol):
    async def get(self, id: int) -> Model | None: ...

class Writable(Protocol):
    async def save(self, entity: Model) -> Model: ...

class ReadOnlyService:
    def __init__(self, repo: Readable) -> None:  # Only needs read
        ...

# Bad - fat interface
class Repository(ABC):
    @abstractmethod
    async def get(self, id: int) -> Model | None: ...
    @abstractmethod
    async def save(self, entity: Model) -> Model: ...
    @abstractmethod
    async def delete(self, id: int) -> None: ...
    @abstractmethod
    async def bulk_insert(self, entities: list[Model]) -> None: ...
```

### D - Dependency Inversion Principle

Depend on abstractions, not concretions.

```python
# Good - depends on abstraction
class SearchService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: EmbeddingProvider,  # Abstract
    ) -> None:
        self.session = session
        self.embedding_provider = embedding_provider

# Bad - depends on concrete implementation
class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.embedding_service = OpenAIEmbedding()  # Concrete, hard to test
```

---

## Code Organization

### Directory Structure

```
app/
├── api/v1/
│   ├── endpoints/      # Route handlers (thin layer)
│   └── router.py       # Route aggregation
├── core/
│   ├── config.py       # Settings and configuration
│   ├── database.py     # Database connection
│   └── auth.py         # Authentication utilities
├── models/             # SQLAlchemy models (data structure)
├── schemas/            # Pydantic schemas (API contracts)
├── services/           # Business logic (the "meat")
└── tasks/              # Background task definitions
```

### Layer Responsibilities

| Layer | Purpose | Dependencies |
|-------|---------|--------------|
| `endpoints/` | HTTP handling, validation, response formatting | Services, Schemas |
| `services/` | Business logic, orchestration | Models, external APIs |
| `models/` | Data structure, relationships | SQLAlchemy Base |
| `schemas/` | API contracts, serialization | Pydantic |
| `core/` | Cross-cutting concerns | None (leaf layer) |

### Import Order

```python
# 1. Standard library
import asyncio
from datetime import datetime
from pathlib import Path

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application
from app.core.database import get_db
from app.models import Company
from app.services.search_service import SearchService
```

---

## Writing Patterns

### Async/Await

Always use async for I/O operations.

```python
# Good
async def fetch_issues(company_id: int) -> list[Issue]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Issue).where(Issue.company_id == company_id)
        )
        return list(result.scalars().all())

# Bad - blocking call in async context
async def fetch_issues(company_id: int) -> list[Issue]:
    with SessionLocal() as session:  # Blocking!
        ...
```

### Context Managers

Use for resource management.

```python
# Good
async with httpx.AsyncClient() as client:
    response = await client.get(url)

async with AsyncSessionLocal() as session:
    async with session.begin():
        session.add(entity)
```

### Early Returns

Reduce nesting with guard clauses.

```python
# Good
async def get_company(slug: str) -> Company:
    company = await self._fetch_company(slug)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.is_active:
        raise HTTPException(status_code=410, detail="Company is inactive")

    return company

# Bad - deep nesting
async def get_company(slug: str) -> Company:
    company = await self._fetch_company(slug)
    if company:
        if company.is_active:
            return company
        else:
            raise HTTPException(status_code=410, detail="Company is inactive")
    else:
        raise HTTPException(status_code=404, detail="Company not found")
```

### Dependency Injection (FastAPI)

```python
# Good - injectable dependencies
async def search_issues(
    query: str,
    db: AsyncSession = Depends(get_db),
) -> IssueListResponse:
    service = SearchService(db)
    return await service.search(query)

# For testing, override the dependency
app.dependency_overrides[get_db] = get_test_db
```

### Dataclasses for Internal Data

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ScrapeStats:
    """Immutable result of a scrape operation."""
    repos_created: int
    repos_updated: int
    issues_created: int
    issues_updated: int
    issues_closed: int
```

---

## Error Handling

### Use Specific Exceptions

```python
# Good - custom exceptions
class GitHubAPIError(Exception):
    """Raised when GitHub API returns an error."""
    def __init__(self, message: str, status_code: int) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class RateLimitExceeded(GitHubAPIError):
    """Raised when GitHub rate limit is hit."""
    pass

# Usage
try:
    data = await client.fetch_repos(org)
except RateLimitExceeded:
    logger.warning("Rate limit hit, waiting...")
    await asyncio.sleep(60)
except GitHubAPIError as e:
    logger.error(f"GitHub API error: {e.message}")
    raise
```

### Don't Swallow Exceptions

```python
# Good - log and re-raise or handle explicitly
try:
    result = await dangerous_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise HTTPException(status_code=400, detail=str(e))

# Bad - silent failure
try:
    result = await dangerous_operation()
except Exception:
    pass  # What happened? We'll never know.
```

### Use HTTPException for API Errors

```python
from fastapi import HTTPException

async def get_issue(issue_id: int) -> IssueResponse:
    issue = await service.get_by_id(issue_id)
    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"Issue with id {issue_id} not found"
        )
    return IssueResponse.model_validate(issue)
```

---

## Testing

### Test Naming

```python
# Pattern: test_<what>_<scenario>_<expected>
def test_search_with_empty_query_returns_all_issues(): ...
def test_sync_company_with_invalid_org_raises_error(): ...
def test_cache_get_expired_entry_returns_none(): ...
```

### Arrange-Act-Assert

```python
async def test_search_returns_cached_results():
    # Arrange
    cache = SearchCache()
    cache.set("python", {}, [1, 2, 3])

    # Act
    result = cache.get("python", {})

    # Assert
    assert result == [1, 2, 3]
```

### Use Fixtures

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_company() -> Company:
    return Company(
        name="Test Corp",
        slug="test-corp",
        github_org="testcorp",
    )

async def test_create_company(db_session: AsyncSession, sample_company: Company):
    db_session.add(sample_company)
    await db_session.commit()

    result = await db_session.get(Company, sample_company.id)
    assert result.name == "Test Corp"
```

---

## Running Quality Checks
- After every code change, check the typing quality and compilation errors

### Type Checking

```bash
# Run mypy
mypy app/

# Check specific file
mypy app/services/search_service.py
```

### Linting and Formatting

```bash
# Check for issues
ruff check app/

# Auto-fix issues
ruff check app/ --fix

# Format code
ruff format app/
```

### All Checks

```bash
# Run everything
ruff check app/ && ruff format --check app/ && mypy app/

# Or create a script
#!/bin/bash
set -e
echo "Running ruff check..."
ruff check app/
echo "Running ruff format check..."
ruff format --check app/
echo "Running mypy..."
mypy app/
echo "All checks passed!"
```

### Pre-commit Hook (Optional)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

Install: `pip install pre-commit && pre-commit install`

---

## Quick Reference

| Do | Don't |
|----|-------|
| `def func(x: int) -> str:` | `def func(x):` |
| `issues: list[Issue]` | `issues: list` |
| `user_count: int` | `uc: int` |
| `is_valid: bool` | `valid: bool` |
| `raise HTTPException(404, ...)` | `return None` for errors |
| `async with session:` | `session = ...` without cleanup |
| Small, focused functions | 100+ line functions |
| Dependency injection | Hard-coded dependencies |
| Early returns | Deep nesting |
| Explicit over implicit | Magic behavior |
