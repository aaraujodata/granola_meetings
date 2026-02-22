"""Shared dependencies: Redis pool, ARQ pool, SearchDB instance."""

import sys
from pathlib import Path

# Ensure repo root is on sys.path for importing src/ and scripts/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from redis.asyncio import Redis

from src.search_db import SearchDB

_redis: Redis | None = None
_arq_pool: ArqRedis | None = None
_search_db: SearchDB | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis(host="localhost", port=6379, decode_responses=True)
    return _redis


async def get_arq_pool() -> ArqRedis:
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings())
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
