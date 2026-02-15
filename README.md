# OSS Issue Finder

A platform that helps developers discover open-source issues to contribute to, without the hassle of manually searching across dozens of GitHub organizations.

It scrapes GitHub issues from curated open-source companies (PostHog, Supabase, Cal.com, etc.), indexes them with AI-powered semantic search, and presents them in a clean, filterable interface.

---

## Table of Contents

- [Why This Project Exists](#why-this-project-exists)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Architecture Decisions](#architecture-decisions)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Prerequisites](#prerequisites)
- [Generating a GitHub Personal Access Token](#generating-a-github-personal-access-token)
- [Getting an OpenAI API Key](#getting-an-openai-api-key)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Adding New Companies](#adding-new-companies)
- [Environment Variables](#environment-variables)
- [Curated Companies](#curated-companies)

---

## Why This Project Exists

Many companies build their products in the open (PostHog, Supabase, Cal.com, etc.), but finding relevant issues to contribute to requires visiting each organization's GitHub, browsing through dozens of repos, and manually filtering issues. This wastes hours.

This platform solves that by:

1. **Aggregating** open issues from 10+ open-source companies into a single interface
2. **Indexing** issues with OpenAI embeddings so you can search semantically (e.g., searching "AI" also finds issues about "machine learning", "neural networks", etc.)
3. **Filtering** by programming language, company, labels ("good first issue", "help wanted"), and star count
4. **Refreshing** data daily via cron jobs, prioritizing consistency over real-time freshness

---

## Architecture Overview

```
                                        +--------------------+
                                        |  GitHub GraphQL    |
                                        |  API               |
                                        +--------+-----------+
                                                 |
                                                 v
+----------------+      +------------------+  +--+---------------+
|                |      |                  |  |                  |
|  Next.js       | ---> |  FastAPI         |  |  Cron Jobs       |
|  Frontend      |      |  Backend         |  |  (sync +         |
|  (port 3000)   |      |  (port 8000)     |  |   embeddings)    |
|                |      |                  |  |                  |
+----------------+      +--------+---------+  +--------+---------+
                                 |                     |
                                 v                     v
                        +--------+---------+  +--------+---------+
                        |                  |  |                  |
                        |  PostgreSQL      |  |  OpenAI          |
                        |  + pgvector      |  |  Embeddings API  |
                        |  (port 5432)     |  |                  |
                        |                  |  |                  |
                        +------------------+  +------------------+
```

**Monorepo layout**: `frontend/` (Next.js) and `backend/` (FastAPI) live side-by-side.

### Data Flow

1. **Cron jobs** trigger the sync script daily at 6 AM
2. **Sync script** calls the GitHub GraphQL API to fetch repos and issues for each curated company
3. Issues are upserted into **PostgreSQL** (new issues created, existing ones updated, closed ones marked stale)
4. A second cron job generates **OpenAI embeddings** for issues that don't have them yet (title + first 500 chars of body)
5. Embeddings are stored in the `issues.embedding` column using **pgvector**
6. The **FastAPI backend** serves paginated, filtered, and semantically-searchable issue data
7. **Search cache** (SQLite with 48h TTL) avoids repeated embedding calls for common queries
8. The **Next.js frontend** renders the UI with search, filters, and issue cards

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------
| Frontend | Next.js | 16 | React framework with App Router + SSR |
| Frontend | Tailwind CSS | 4 | Utility-first CSS |
| Frontend | shadcn/ui | latest | Accessible UI component library |
| Frontend | TanStack React Query | 5 | Server state management + caching |
| Frontend | next-themes | latest | Dark/light theme toggling |
| Frontend | Lucide React | latest | Icon library |
| Backend | FastAPI | 0.115 | Async Python API framework |
| Backend | SQLAlchemy | 2.0 | Async ORM with PostgreSQL |
| Backend | Alembic | 1.14 | Database migrations |
| Backend | httpx | 0.28 | Async HTTP client for GitHub API |
| Backend | OpenAI SDK | 1.58 | Embedding generation |
| Database | PostgreSQL | 16 | Primary data store |
| Database | pgvector | 0.3 | Vector similarity search extension |
| Cache | SQLite | - | Search result cache (48h TTL) |

---

## Architecture Decisions

### Why GitHub GraphQL API instead of Apify or REST API?

We initially considered using the `fresh_cliff/github-scraper` Apify actor, but research revealed it is **repository-focused only** -- it cannot fetch issues or their labels. A dedicated issues actor (`incontrovertible_gate/github-issues-actor`) exists but costs money per run.

The GitHub GraphQL API was chosen because:

- **Free** with a personal access token (5,000 points/hour rate limit)
- **~150x faster** than the REST API for batch operations -- a single query can fetch 100 issues with labels, comments count, and metadata
- **Exact data shape** -- you request only the fields you need, reducing bandwidth
- **Pagination** via cursors, not page numbers, for reliable large-dataset traversal
- **No third-party dependency** -- direct integration with no middleman cost or availability risk

For reference, the REST API is limited to 30 items per page and requires separate calls for issues, labels, and repo metadata. GraphQL collapses all of that into one request.

> GitHub GraphQL API docs: https://docs.github.com/en/graphql

### Why pgvector instead of a dedicated vector database (Pinecone, Weaviate)?

The dataset is relatively small (tens of thousands of issues, not millions). pgvector handles this scale trivially with HNSW indexing, and keeping everything in a single PostgreSQL database eliminates deployment complexity. No need for a separate vector DB service, connection management, or data synchronization.

### Why hybrid search (semantic + keyword) instead of pure semantic?

Two reasons:

1. **Coverage**: Newly scraped issues may not have embeddings yet. Keyword fallback ensures they still appear in search results.
2. **Precision**: If someone searches "OAuth2 bug", an issue literally titled "OAuth2 bug in login flow" should rank at the top, even if another issue is semantically similar but uses different words.

The scoring formula is: `combined_score = 0.6 * semantic_score + 0.4 * keyword_score`

### Why cron jobs instead of Celery + Redis?

For a personal project, Celery + Redis adds unnecessary complexity:

- **Simpler deployment**: No Redis server, no worker processes, no beat scheduler
- **Easier debugging**: Plain Python scripts you can run directly
- **Lower resource usage**: No always-on worker processes
- **Sufficient for the use case**: Daily syncs don't need distributed task queues

The sync runs via standard cron:
```bash
# Daily at 6:00 AM
0 6 * * * cd /app && python -m scripts.sync

# Embeddings at 6:30 AM
30 6 * * * cd /app && python -m scripts.generate_embeddings
```

### Why tiered search with caching?

Not every query needs the full embedding pipeline:

1. **Tier 1 - Cache hit**: Returns instantly, R$0 cost
2. **Tier 2 - Simple keywords**: Queries like "Python", "React" use SQL LIKE search, R$0 cost
3. **Tier 3 - Semantic search**: Complex queries use OpenAI embeddings

A SQLite cache with 48h TTL stores search results, so repeated searches for common terms don't hit the embedding API.

### Why consistency over real-time freshness?

The sync runs daily instead of continuously because:

- GitHub API rate limits (5,000 points/hour) would be exhausted quickly with real-time polling across 10+ orgs
- Issues don't change that frequently -- a 24-hour window is acceptable for discovery
- Batch processing is more reliable and easier to monitor than streaming updates
- Embedding generation is a separate step that benefits from batching

### Why `ARRAY(String)` for labels instead of a join table?

GitHub issues have a small, bounded number of labels (typically < 10). A PostgreSQL array column is simpler to query (using the `&&` overlap operator for filtering), avoids N+1 queries, and mirrors the shape of the data from the GraphQL API. A separate `label_details` JSONB column stores the full label objects (name, color, description) for display.

### Why OpenAI `text-embedding-3-small` for embeddings?

- 1536 dimensions, good balance of quality vs. size
- Costs ~$0.02 per 1M tokens (very affordable at our scale)
- For 50k issues with title + 500 chars of body (~80 words avg), total embedding cost is ~$0.05

Each embedding is generated from `"{title} {body[:500]}"` -- including the first 500 characters of the issue body gives the model richer semantic context without excessive cost or noise.

---

## Project Structure

```
search-open-source-issues/
|-- .env.example                    # Environment variable template
|-- .gitignore
|-- docker-compose.yml              # Services (db, backend)
|-- implementation-plan.md          # Detailed implementation plan
|-- README.md                       # This file
|
|-- backend/
|   |-- Dockerfile
|   |-- Procfile                    # Web process only
|   |-- requirements.txt
|   |-- requirements-dev.txt        # Test dependencies
|   |-- alembic.ini                 # Migration config
|   |-- alembic/
|   |   |-- env.py                  # Async migration environment
|   |   |-- script.py.mako
|   |   |-- versions/
|   |       |-- 001_initial_schema.py
|   |
|   |-- scripts/
|   |   |-- sync.py                 # Standalone sync script for cron
|   |   |-- generate_embeddings.py  # Standalone embeddings script for cron
|   |   |-- crontab                 # Cron configuration example
|   |
|   |-- app/
|       |-- main.py                 # FastAPI app entrypoint
|       |-- seed.py                 # Seed 10 curated companies
|       |
|       |-- core/
|       |   |-- config.py           # Pydantic Settings (env vars)
|       |   |-- database.py         # Async SQLAlchemy engine + session
|       |
|       |-- models/
|       |   |-- base.py             # DeclarativeBase + TimestampMixin
|       |   |-- company.py          # Company model
|       |   |-- repository.py       # Repository model
|       |   |-- issue.py            # Issue model (with pgvector embedding)
|       |
|       |-- schemas/
|       |   |-- issue.py            # IssueResponse, IssueListResponse, etc.
|       |   |-- company.py          # CompanyResponse
|       |   |-- stats.py            # StatsResponse
|       |   |-- admin.py            # CreateCompanyRequest, UpdateCompanyRequest
|       |
|       |-- api/v1/
|       |   |-- router.py           # Aggregates all endpoint routers
|       |   |-- endpoints/
|       |       |-- issues.py       # GET /issues/, GET /issues/{id}
|       |       |-- companies.py    # GET /companies/, GET /companies/{slug}
|       |       |-- search.py       # GET /search/?q=...
|       |       |-- stats.py        # GET /stats/
|       |       |-- admin.py        # POST/PUT/DELETE /admin/companies/
|       |
|       |-- services/
|       |   |-- github_client.py    # GitHub GraphQL API client
|       |   |-- scraper.py          # Scraping orchestrator
|       |   |-- embedding_service.py # OpenAI embedding generation
|       |   |-- search_service.py   # Tiered search (cache → keyword → semantic)
|       |   |-- search_cache.py     # SQLite cache with 48h TTL
|       |   |-- issue_service.py    # Issue queries with filters/pagination
|       |   |-- stats_service.py    # Aggregate statistics queries
|       |
|       |-- tasks/
|           |-- sync.py             # Sync functions (called by cron script)
|           |-- embeddings.py       # Embedding functions (called by cron script)
|
|-- frontend/
    |-- Dockerfile
    |-- package.json
    |-- tsconfig.json
    |-- next.config.ts
    |-- components.json             # shadcn/ui configuration
    |
    |-- src/
        |-- app/
        |   |-- globals.css         # Tailwind + dark theme CSS variables
        |   |-- layout.tsx          # Root layout (fonts, metadata, providers)
        |   |-- page.tsx            # Home page
        |   |-- providers.tsx       # ThemeProvider + QueryClientProvider
        |
        |-- components/
        |   |-- ui/                 # shadcn/ui components (auto-generated)
        |   |-- layout/header.tsx   # Top nav bar with Cmd+K trigger
        |   |-- hero-section.tsx    # Title and subtitle
        |   |-- issues-browser.tsx  # Main orchestrator (search + filters + list)
        |   |-- issues/
        |   |   |-- issue-card.tsx  # Single issue card
        |   |   |-- issue-list.tsx  # List of cards with loading skeletons
        |   |   |-- issue-filters.tsx # Collapsible filter panel
        |   |-- search/
        |   |   |-- search-bar.tsx  # Main search input
        |   |   |-- search-command.tsx # Cmd+K command palette
        |   |-- stats/
        |   |   |-- stats-bar.tsx   # Language badge summary bar
        |   |-- common/
        |       |-- language-badge.tsx
        |       |-- label-badge.tsx
        |       |-- company-avatar.tsx
        |       |-- pagination.tsx
        |
        |-- lib/
        |   |-- api.ts              # Fetch wrapper for backend
        |   |-- types.ts            # TypeScript interfaces
        |   |-- constants.ts        # Language colors, label presets
        |   |-- utils.ts            # Utility functions (cn)
        |
        |-- hooks/
            |-- use-issues.ts       # React Query: list + search issues
            |-- use-companies.ts    # React Query: list companies
            |-- use-stats.ts        # React Query: platform stats
            |-- use-debounce.ts     # Debounce hook (300ms)
```

---

## Database Schema

Three tables with clear foreign key relationships:

```
companies (1) ----< repositories (1) ----< issues
```

### companies

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Unique, indexed |
| slug | VARCHAR(255) | URL-safe identifier, unique |
| logo_url | VARCHAR(512) | GitHub avatar URL |
| website | VARCHAR(512) | Company website |
| description | TEXT | Short description |
| github_org | VARCHAR(255) | GitHub org login, unique |
| created_at | TIMESTAMPTZ | Auto-set |
| updated_at | TIMESTAMPTZ | Auto-updated |

### repositories

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | Primary key |
| github_id | INTEGER | GitHub's internal ID, unique |
| name | VARCHAR(255) | Repo name (e.g., "posthog") |
| full_name | VARCHAR(512) | Owner/repo (e.g., "PostHog/posthog"), unique |
| description | TEXT | Repo description |
| url | VARCHAR(512) | GitHub URL |
| primary_language | VARCHAR(100) | Indexed for filtering |
| stars | INTEGER | Star count |
| forks | INTEGER | Fork count |
| topics | TEXT[] | PostgreSQL array of topic strings |
| company_id | INTEGER FK | References companies.id |

### issues

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL | Primary key |
| github_id | INTEGER | GitHub's internal ID, unique |
| number | INTEGER | Issue number (e.g., #1234) |
| title | TEXT | Issue title |
| body | TEXT | Issue body (nullable) |
| url | VARCHAR(512) | Direct link to GitHub issue |
| state | VARCHAR(20) | "OPEN" or "CLOSED", indexed |
| labels | TEXT[] | Flat array of label names for filtering |
| label_details | JSONB | Array of {name, color, description} for display |
| comment_count | INTEGER | Number of comments |
| github_created_at | TIMESTAMPTZ | When the issue was created on GitHub |
| github_updated_at | TIMESTAMPTZ | Last update time on GitHub |
| repository_id | INTEGER FK | References repositories.id |
| embedding | VECTOR(1536) | pgvector column with HNSW index for semantic search |

---

## API Endpoints

Base URL: `http://localhost:8000`

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/issues/` | GET | List open issues (paginated, filterable) |
| `/api/v1/issues/{id}` | GET | Single issue detail |
| `/api/v1/companies/` | GET | List all companies with repo/issue counts |
| `/api/v1/companies/{slug}` | GET | Single company detail |
| `/api/v1/search/?q=...` | GET | Hybrid semantic + keyword search |
| `/api/v1/stats/` | GET | Aggregate stats (totals, languages, labels) |
| `/api/v1/admin/companies/` | POST | Add a new company |
| `/api/v1/admin/companies/{slug}` | PUT | Update company details |
| `/api/v1/admin/companies/{slug}` | DELETE | Remove a company and all its data |

### Query Parameters for `/api/v1/issues/`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (1-based) |
| `page_size` | int | 20 | Items per page (max 100) |
| `language` | string[] | - | Filter by programming language (repeatable) |
| `company` | string[] | - | Filter by company slug (repeatable) |
| `label` | string[] | - | Filter by label name (repeatable) |
| `min_stars` | int | - | Minimum repository star count |
| `sort_by` | string | "updated" | Sort field: "updated", "created", or "stars" |
| `sort_order` | string | "desc" | Sort direction: "asc" or "desc" |

### Example Requests

```bash
# List all open issues, most recently updated first
curl "http://localhost:8000/api/v1/issues/"

# Filter by Python + "good first issue" label
curl "http://localhost:8000/api/v1/issues/?language=Python&label=good+first+issue"

# Semantic search for AI-related issues
curl "http://localhost:8000/api/v1/search/?q=machine+learning"

# Get platform stats
curl "http://localhost:8000/api/v1/stats/"

# Add a new company via admin API
curl -X POST "http://localhost:8000/api/v1/admin/companies/" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your_admin_key" \
  -d '{"name": "Grafana", "github_org": "grafana", "website": "https://grafana.com", "description": "Open source observability platform"}'
```

---

## Prerequisites

Before starting, make sure you have:

- **Docker** and **Docker Compose** (v2+) installed
- A **GitHub Personal Access Token** (see section below)
- An **OpenAI API Key** (see section below)
- **Node.js 20+** and **npm** (only needed if running frontend outside Docker)
- **Python 3.11+** (only needed if running backend outside Docker)

---

## Generating a GitHub Personal Access Token

The GitHub GraphQL API requires authentication via a Personal Access Token (PAT). The token is used to fetch repository metadata and issues from GitHub organizations.

### Rate Limits

| Authentication | Rate Limit |
|---------------|------------|
| No token | 60 requests/hour (unusable for this project) |
| With PAT | 5,000 points/hour (sufficient for 10+ orgs) |

### Step-by-Step: Creating a Fine-Grained Token

1. Go to **GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens**

   Direct link: https://github.com/settings/tokens?type=beta

2. Click **"Generate new token"**

3. Fill in the form:
   - **Token name**: `oss-issue-finder` (or any name you prefer)
   - **Expiration**: Choose a duration (90 days is a good default)
   - **Description**: Optional, e.g., "Token for OSS Issue Finder scraper"

4. Under **Repository access**, select **"Public Repositories (read-only)"**

   This is all the project needs -- it only reads public repositories and their issues.

5. Under **Permissions**, no additional permissions are needed beyond the default public repo read access. The GraphQL API uses this token purely for authentication and rate limit allocation.

6. Click **"Generate token"**

7. **Copy the token immediately** -- it won't be shown again. It starts with `github_pat_` for fine-grained tokens.

### Alternative: Classic Token

If you prefer a classic token:

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Select the **`public_repo`** scope only
4. Generate and copy the token (starts with `ghp_`)

### Useful GitHub API Documentation

- **GraphQL API overview**: https://docs.github.com/en/graphql
- **GraphQL Explorer** (interactive): https://docs.github.com/en/graphql/overview/explorer
- **Authentication for GraphQL**: https://docs.github.com/en/graphql/guides/forming-calls-with-graphql#authenticating-with-graphql
- **Rate limits for GraphQL**: https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api
- **REST vs GraphQL comparison**: https://docs.github.com/en/rest/about-the-rest-api/comparing-githubs-rest-api-and-graphql-api

### Verifying Your Token

After generating, verify it works:

```bash
curl -H "Authorization: bearer YOUR_TOKEN_HERE" \
  -X POST \
  -d '{"query": "{ viewer { login } }"}' \
  https://api.github.com/graphql
```

You should see a response with your GitHub username.

---

## Getting an OpenAI API Key

The OpenAI API is used to generate embeddings for semantic search. The model used is `text-embedding-3-small`.

1. Go to https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Copy the key (starts with `sk-`)
4. Add billing at https://platform.openai.com/settings/organization/billing/overview

**Cost estimate**: For 50,000 issues with title + body text, embedding generation costs approximately **$0.05 total** (~$0.02 per 1M tokens).

---

## Installation & Setup

### Prerequisites

- Docker and Docker Compose
- Git

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd search-open-source-issues
```

### Step 2: Create environment file

```bash
cp .env.example .env
```

Edit `.env` and fill in your tokens:

```env
GITHUB_TOKEN=github_pat_your_token_here
OPENAI_API_KEY=sk-your_key_here
DATABASE_URL=postgresql+asyncpg://ossearch:ossearch_dev@db:5432/ossearch
ADMIN_API_KEY=your_secret_admin_key
```

> **Note**: The `DATABASE_URL` above uses the Docker service name (`db`) and works for Docker setup.

### Step 3: Start the stack

```bash
docker compose up --build -d
```

This starts PostgreSQL and the backend API.

### Step 4: Run database migrations and seed

Once the containers are running:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

You should see output like:

```
Seeded 10 companies:
  - PostHog (PostHog)
  - Supabase (supabase)
  - Cal.com (calcom)
  ...
```

### Step 5: Run the initial sync

```bash
docker compose exec backend python -m scripts.sync
```

This fetches all repos and issues from GitHub for the seeded companies.

### Step 6: Generate embeddings

After the sync completes:

```bash
docker compose exec backend python -m scripts.generate_embeddings
```

### Step 7: Open the app

- **Frontend**: http://localhost:3000
- **Backend API docs**: http://localhost:8000/docs

---

### Alternative: Local Development Setup

If you prefer to run the backend and frontend locally (with hot reload) while keeping only the database in Docker:

**Additional prerequisites**: Python 3.11+, Node.js 20+

**1. Start only the database:**

```bash
docker compose up db -d
```

**2. Update `.env` to use `localhost` instead of Docker service names:**

```env
DATABASE_URL=postgresql+asyncpg://ossearch:ossearch_dev@localhost:5432/ossearch
```

**3. Set up and start the backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**4. Run sync and embeddings manually:**

```bash
cd backend && source .venv/bin/activate
python -m scripts.sync
python -m scripts.generate_embeddings
```

**5. Set up and start the frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Setting Up Cron Jobs (Production)

For automated daily syncs, add these to your crontab (`crontab -e`):

```bash
# Sync all companies daily at 6:00 AM
0 6 * * * cd /path/to/backend && /path/to/python -m scripts.sync >> /var/log/ossearch/sync.log 2>&1

# Generate embeddings at 6:30 AM
30 6 * * * cd /path/to/backend && /path/to/python -m scripts.generate_embeddings >> /var/log/ossearch/embeddings.log 2>&1
```

---

## Usage

### Browsing Issues

- Open http://localhost:3000
- Issues are displayed as cards with company name, repository, title, labels, language, star count, and comment count
- Click any issue title to open it directly on GitHub

### Searching

- **Search bar**: Type any keyword in the search bar. Results update after 300ms of inactivity (debounced)
- **Cmd+K** (or Ctrl+K): Opens a quick-search command palette for fast issue lookup
- **Semantic search**: Searching "AI" will also return issues about "machine learning", "neural networks", etc., thanks to OpenAI embeddings
- **Tiered search**: Simple keywords (Python, React) use fast SQL search; complex queries use semantic search

### Filtering

- **Language badges**: Click the language pills at the top (e.g., "Python (364)") to toggle language filters
- **Filters panel**: Expand the "Filters" section to filter by:
  - Programming language
  - Company
  - Labels ("good first issue", "help wanted", "bug", "enhancement", "documentation", "hacktoberfest")
- **Clear filters**: Click the "Clear filters" button to reset all active filters

### Sorting

Issues are sorted by "Recently updated" by default. You can change sorting via the API query parameters (`sort_by=stars`, `sort_by=created`).

---

## Adding New Companies

You can add companies dynamically through the admin API:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/companies/" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your_admin_key" \
  -d '{
    "name": "Grafana",
    "github_org": "grafana",
    "website": "https://grafana.com",
    "description": "Open source observability platform"
  }'
```

This will:
1. Create the company record
2. Automatically set the logo URL from GitHub
3. Trigger an initial sync to populate repos and issues (runs in background)

To remove a company:

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/companies/grafana" \
  -H "X-Admin-Key: your_admin_key"
```

You can also add companies directly in `backend/app/seed.py` and re-run the seed script.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | - | GitHub PAT for GraphQL API access |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for embedding generation |
| `DATABASE_URL` | No | `postgresql+asyncpg://ossearch:ossearch_dev@localhost:5432/ossearch` | PostgreSQL connection string |
| `ADMIN_API_KEY` | Yes | - | Secret key for admin API endpoints |
| `ISSUES_PER_REPO` | No | `100` | Max open issues to fetch per repository |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend URL for the frontend |

---

## Curated Companies

The platform ships with 10 pre-configured open-source companies:

| Company | GitHub Org | Description |
|---------|-----------|-------------|
| PostHog | [PostHog](https://github.com/PostHog) | Open source product analytics |
| Supabase | [supabase](https://github.com/supabase) | Open source Firebase alternative |
| Cal.com | [calcom](https://github.com/calcom) | Open source scheduling infrastructure |
| Infisical | [Infisical](https://github.com/Infisical) | Open source secret management |
| Novu | [novuhq](https://github.com/novuhq) | Open source notification infrastructure |
| Appsmith | [appsmithorg](https://github.com/appsmithorg) | Open source low-code platform |
| Hoppscotch | [hoppscotch](https://github.com/hoppscotch) | Open source API development ecosystem |
| Formbricks | [formbricks](https://github.com/formbricks) | Open source survey platform |
| Medusa | [medusajs](https://github.com/medusajs) | Open source digital commerce platform |
| Plane | [makeplane](https://github.com/makeplane) | Open source project management |

Add more via the admin API or by editing `backend/app/seed.py`.
