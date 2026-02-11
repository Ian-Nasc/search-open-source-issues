import httpx

from app.core.config import settings

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


class GitHubGraphQLClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Content-Type": "application/json",
        }

    async def execute(self, query: str, variables: dict | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_GRAPHQL_URL,
                json={"query": query, "variables": variables or {}},
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            return data["data"]

    async def fetch_org_repositories(
        self, org: str, cursor: str | None = None
    ) -> dict:
        query = """
        query($org: String!, $cursor: String) {
            organization(login: $org) {
                repositories(
                    first: 50,
                    after: $cursor,
                    orderBy: {field: STARGAZERS, direction: DESC},
                    isFork: false
                ) {
                    pageInfo { hasNextPage endCursor }
                    nodes {
                        databaseId
                        name
                        nameWithOwner
                        description
                        url
                        primaryLanguage { name }
                        stargazerCount
                        forkCount
                        repositoryTopics(first: 20) {
                            nodes { topic { name } }
                        }
                        isArchived
                    }
                }
            }
        }
        """
        return await self.execute(query, {"org": org, "cursor": cursor})

    async def fetch_repo_issues(
        self,
        owner: str,
        repo: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> dict:
        query = """
        query($owner: String!, $repo: String!, $cursor: String, $limit: Int!) {
            repository(owner: $owner, name: $repo) {
                issues(
                    first: $limit,
                    after: $cursor,
                    states: [OPEN],
                    orderBy: {field: UPDATED_AT, direction: DESC}
                ) {
                    pageInfo { hasNextPage endCursor }
                    totalCount
                    nodes {
                        databaseId
                        number
                        title
                        body
                        url
                        state
                        createdAt
                        updatedAt
                        comments { totalCount }
                        labels(first: 10) {
                            nodes { name color description }
                        }
                    }
                }
            }
        }
        """
        return await self.execute(
            query,
            {
                "owner": owner,
                "repo": repo,
                "cursor": cursor,
                "limit": min(limit, 100),
            },
        )

    async def fetch_all_org_repositories(self, org: str) -> list[dict]:
        all_repos = []
        cursor = None
        while True:
            data = await self.fetch_org_repositories(org, cursor)
            org_data = data.get("organization")
            if not org_data:
                break
            repos = org_data["repositories"]
            nodes = repos["nodes"]
            for node in nodes:
                if node["isArchived"]:
                    continue
                if node["stargazerCount"] < 10:
                    continue
                all_repos.append(node)
            page_info = repos["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        return all_repos

    async def fetch_all_repo_issues(
        self, owner: str, repo: str, max_issues: int = 100
    ) -> list[dict]:
        all_issues = []
        cursor = None
        while len(all_issues) < max_issues:
            batch_size = min(100, max_issues - len(all_issues))
            data = await self.fetch_repo_issues(owner, repo, cursor, batch_size)
            repo_data = data.get("repository")
            if not repo_data:
                break
            issues = repo_data["issues"]
            all_issues.extend(issues["nodes"])
            page_info = issues["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        return all_issues
