from fastapi import Header, HTTPException

from app.core.config import settings


async def verify_admin_key(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    """Verify the admin API key from request header."""
    if not settings.ADMIN_API_KEY or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True
