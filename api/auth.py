"""
API key authentication.

  X-API-Key header:
    - API_READ_KEY  → /ask, /config
    - API_ADMIN_KEY → /index (also grants read access)

  /health is always public (for load balancers).

If API_AUTH_ENABLED=false, all endpoints are open (local dev).
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from config.settings import load_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _auth_enabled() -> bool:
    settings = load_settings()
    return settings.api_auth_enabled


def _validate_key(provided: str | None, required: str | None, label: str) -> None:
    if not required:
        return
    if not provided or provided != required:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or missing API key. Provide a valid {label} via X-API-Key header.",
        )


def require_read_key(api_key: str | None = Security(_api_key_header)) -> None:
    """Allow read operations with API_READ_KEY or API_ADMIN_KEY."""
    if not _auth_enabled():
        return

    settings = load_settings()
    if not settings.api_read_key and not settings.api_admin_key:
        return

    if settings.api_admin_key and api_key == settings.api_admin_key:
        return
    _validate_key(api_key, settings.api_read_key, "API_READ_KEY")


def require_admin_key(api_key: str | None = Security(_api_key_header)) -> None:
    """Allow admin operations only with API_ADMIN_KEY."""
    if not _auth_enabled():
        return

    settings = load_settings()
    if not settings.api_admin_key:
        if not settings.api_read_key:
            return
        raise HTTPException(
            status_code=503,
            detail="API_ADMIN_KEY is not configured. Set it in .env to enable indexing via API.",
        )

    _validate_key(api_key, settings.api_admin_key, "API_ADMIN_KEY")
