import asyncio
import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import AsyncSessionLocal
from app.models import Company

COMPANIES = [
    {
        "name": "PostHog",
        "slug": "posthog",
        "github_org": "PostHog",
        "logo_url": "https://avatars.githubusercontent.com/u/61585353",
        "website": "https://posthog.com",
        "description": "Open source product analytics",
    },
    {
        "name": "Supabase",
        "slug": "supabase",
        "github_org": "supabase",
        "logo_url": "https://avatars.githubusercontent.com/u/54469796",
        "website": "https://supabase.com",
        "description": "Open source Firebase alternative",
    },
    {
        "name": "Cal.com",
        "slug": "calcom",
        "github_org": "calcom",
        "logo_url": "https://avatars.githubusercontent.com/u/79145102",
        "website": "https://cal.com",
        "description": "Open source scheduling infrastructure",
    },
    {
        "name": "Infisical",
        "slug": "infisical",
        "github_org": "Infisical",
        "logo_url": "https://avatars.githubusercontent.com/u/107880645",
        "website": "https://infisical.com",
        "description": "Open source secret management",
    },
    {
        "name": "Novu",
        "slug": "novu",
        "github_org": "novuhq",
        "logo_url": "https://avatars.githubusercontent.com/u/77433905",
        "website": "https://novu.co",
        "description": "Open source notification infrastructure",
    },
    {
        "name": "Appsmith",
        "slug": "appsmith",
        "github_org": "appsmithorg",
        "logo_url": "https://avatars.githubusercontent.com/u/67620218",
        "website": "https://appsmith.com",
        "description": "Open source low-code platform",
    },
    {
        "name": "Hoppscotch",
        "slug": "hoppscotch",
        "github_org": "hoppscotch",
        "logo_url": "https://avatars.githubusercontent.com/u/56705483",
        "website": "https://hoppscotch.io",
        "description": "Open source API development ecosystem",
    },
    {
        "name": "Formbricks",
        "slug": "formbricks",
        "github_org": "formbricks",
        "logo_url": "https://avatars.githubusercontent.com/u/105877416",
        "website": "https://formbricks.com",
        "description": "Open source survey platform",
    },
    {
        "name": "Medusa",
        "slug": "medusa",
        "github_org": "medusajs",
        "logo_url": "https://avatars.githubusercontent.com/u/58062887",
        "website": "https://medusajs.com",
        "description": "Open source digital commerce platform",
    },
    {
        "name": "Plane",
        "slug": "plane",
        "github_org": "makeplane",
        "logo_url": "https://avatars.githubusercontent.com/u/115727700",
        "website": "https://plane.so",
        "description": "Open source project management",
    },
]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def seed_companies():
    async with AsyncSessionLocal() as session:
        for company_data in COMPANIES:
            stmt = (
                insert(Company)
                .values(**company_data)
                .on_conflict_do_update(
                    index_elements=["github_org"],
                    set_={
                        "name": company_data["name"],
                        "logo_url": company_data["logo_url"],
                        "website": company_data["website"],
                        "description": company_data["description"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

        result = await session.execute(select(Company))
        companies = result.scalars().all()
        print(f"Seeded {len(companies)} companies:")
        for c in companies:
            print(f"  - {c.name} ({c.github_org})")


if __name__ == "__main__":
    asyncio.run(seed_companies())
