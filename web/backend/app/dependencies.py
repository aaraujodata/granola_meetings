"""Shared dependencies: Redis pool, ARQ pool, SearchDB instance."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Ensure repo root is on sys.path for importing src/ and scripts/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from redis.asyncio import Redis

from src.search_db import SearchDB

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

_redis: Redis | None = None
_arq_pool: ArqRedis | None = None
_search_db: SearchDB | None = None


def _parse_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into ARQ RedisSettings."""
    parsed = urlparse(REDIS_URL)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
    )


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def get_arq_pool() -> ArqRedis:
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(_parse_redis_settings())
    return _arq_pool


async def close_redis():
    global _redis, _arq_pool
    if _arq_pool is not None:
        await _arq_pool.aclose()
        _arq_pool = None
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_search_db() -> SearchDB:
    global _search_db
    if _search_db is None:
        _search_db = SearchDB()
        _search_db.initialize()
    return _search_db
