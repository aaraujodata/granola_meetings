"""FastAPI application: CORS, lifespan, router includes."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_redis, close_redis
from app.routers import meetings, search, pipeline, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up Redis connection
    await get_redis()
    yield
    # Shutdown: close Redis
    await close_redis()


app = FastAPI(
    title="Granola Meetings API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(status.router, prefix="/api")
