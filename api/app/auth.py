import httpx
from fastapi import HTTPException
from .config import get_settings

async def require_user(authorization: str | None) -> dict:
    settings = get_settings()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in to use chat.")
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status_code=503, detail="Supabase authentication is not configured.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/user", headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"})
        if response.status_code != 200: raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
        return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Authentication service is temporarily unavailable.") from exc

