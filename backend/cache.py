"""
Redis cache layer.

Usage:
    from backend.cache import cache_get, cache_set, cache_delete, invalidate_prefix

Keys are namespaced with a prefix to avoid collisions.
TTL defaults to 60 seconds.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis_client = None


def _get_client():
    """Lazy-init Redis connection. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis as redis_lib
        from backend.config import settings
        _redis_client = redis_lib.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        _redis_client.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis unavailable (%s) — caching disabled.", exc)
        _redis_client = None
    return _redis_client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cache_get(key: str) -> Optional[Any]:
    """Return cached value or None (falls back gracefully if Redis is down)."""
    client = _get_client()
    if client is None:  # pragma: no cover
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:  # pragma: no cover
        logger.debug("cache_get error: %s", exc)
        return None


def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    """Store value in cache with a TTL (seconds). Fails silently."""
    client = _get_client()
    if client is None:  # pragma: no cover
        return
    try:
        client.setex(key, ttl, json.dumps(value))
    except Exception as exc:  # pragma: no cover
        logger.debug("cache_set error: %s", exc)


def cache_delete(key: str) -> None:
    """Delete a single key."""
    client = _get_client()
    if client is None:  # pragma: no cover
        return
    try:
        client.delete(key)
    except Exception as exc:  # pragma: no cover
        logger.debug("cache_delete error: %s", exc)


def invalidate_prefix(prefix: str) -> int:
    """Delete all keys matching prefix:*. Returns number of keys deleted."""
    client = _get_client()
    if client is None:  # pragma: no cover
        return 0
    try:
        keys = client.keys(f"{prefix}:*")
        if keys:
            return client.delete(*keys)
    except Exception as exc:  # pragma: no cover
        logger.debug("invalidate_prefix error: %s", exc)
    return 0


def reset_client() -> None:
    """Force a new connection on next use (for testing)."""
    global _redis_client
    _redis_client = None
