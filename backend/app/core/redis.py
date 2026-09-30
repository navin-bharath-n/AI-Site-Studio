"""
Redis client — async connection pool and caching subsystem via redis-py.
Provides robust cache read/write/invalidation helpers with graceful
fallback when Redis is unavailable.
"""

import json
import hashlib
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger("cache.redis")

_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Return the shared async Redis client (singleton) or None if unavailable."""
    global _redis_client
    if _redis_client is None:
        url = (settings.REDIS_URL or "").strip()
        if not url or not any(url.startswith(scheme) for scheme in ("redis://", "rediss://", "unix://")):
            logger.info(f"[Redis Cache] REDIS_URL not configured or invalid scheme. Running without Redis cache.")
            return None
        try:
            _redis_client = aioredis.from_url(
                url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
        except Exception as e:
            logger.warning(f"[Redis Cache] Failed to initialize Redis from URL: {e}. Running without Redis.")
            _redis_client = None
    return _redis_client


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency for Redis access."""
    return await get_redis_client()


def _json_serial(obj: Any) -> Any:
    """JSON serializer helper for UUIDs, Decimals, dates/times, and Pydantic models."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


import time
import fnmatch

# L1 In-Memory High-Speed Cache (Fast RAM lookup: <0.1ms, zero network latency)
_memory_cache: dict[str, tuple[float, Any]] = {}


async def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve from L1 memory cache first; fall back to L2 Redis cache.
    Returns None on cache miss.
    """
    now = time.time()
    # 1. Fast L1 RAM check
    if key in _memory_cache:
        expire_at, val = _memory_cache[key]
        if now < expire_at:
            return val
        _memory_cache.pop(key, None)

    # 2. L2 Redis check
    try:
        client = await get_redis_client()
        if not client:
            return None
        raw = await client.get(key)
        if raw is not None:
            val = json.loads(raw)
            # Promote to L1 memory cache for 60 seconds
            _memory_cache[key] = (now + 60, val)
            return val
    except Exception as e:
        logger.debug(f"[Redis Cache] cache_get('{key}') missed/failed: {e}")
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Store in L1 memory cache and L2 Redis cache with TTL.
    """
    now = time.time()
    # 1. Store in L1 memory cache
    try:
        _memory_cache[key] = (now + ttl, value)
        if len(_memory_cache) > 2000:
            # Clean expired items
            expired = [k for k, (exp, _) in _memory_cache.items() if now >= exp]
            for k in expired:
                _memory_cache.pop(k, None)
    except Exception:
        pass

    # 2. Store in L2 Redis
    try:
        client = await get_redis_client()
        if not client:
            return True
        payload = json.dumps(value, default=_json_serial)
        await client.set(key, payload, ex=ttl)
        return True
    except Exception as e:
        logger.debug(f"[Redis Cache] cache_set('{key}') failed: {e}")
        return True


async def cache_delete(key: str) -> bool:
    """
    Invalidate key from both L1 memory cache and L2 Redis.
    """
    _memory_cache.pop(key, None)
    try:
        client = await get_redis_client()
        if client:
            await client.delete(key)
        return True
    except Exception as e:
        logger.debug(f"[Redis Cache] cache_delete('{key}') failed: {e}")
        return True


async def cache_delete_pattern(pattern: str) -> bool:
    """
    Invalidate all keys matching glob pattern in both L1 memory and L2 Redis.
    """
    now = time.time()
    to_delete = [k for k in _memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
    for k in to_delete:
        _memory_cache.pop(k, None)

    try:
        client = await get_redis_client()
        if client:
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
        return True
    except Exception as e:
        logger.debug(f"[Redis Cache] cache_delete_pattern('{pattern}') failed: {e}")
        return True


class CacheKeys:
    """Centralized, deterministic cache key builder."""

    @staticmethod
    def template(slug: str) -> str:
        return f"template:{slug}"

    @staticmethod
    def template_list(page: int, filters: str) -> str:
        return f"templates:list:{page}:{filters}"

    @staticmethod
    def featured(limit: int = 8) -> str:
        return f"templates:featured:{limit}"

    @staticmethod
    def categories() -> str:
        return "categories:all"

    @staticmethod
    def user_favorites(user_id: str) -> str:
        return f"user:{user_id}:favorites"

    @staticmethod
    def user_wishlist(user_id: str) -> str:
        return f"user:{user_id}:wishlist"

    @staticmethod
    def search(query: str, filters: str = "") -> str:
        # Deterministic MD5 hash independent of python process seed
        digest = hashlib.md5(f"{query.lower().strip()}:{filters}".encode("utf-8")).hexdigest()[:16]
        return f"search:{digest}"

    CACHE_TTL_SHORT = 60       # 1 minute
    CACHE_TTL_MEDIUM = 300     # 5 minutes
    CACHE_TTL_LONG = 3600      # 1 hour
    CACHE_TTL_DAY = 86400      # 24 hours
