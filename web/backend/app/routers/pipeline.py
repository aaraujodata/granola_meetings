"""Pipeline router: trigger async jobs and check status."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import get_redis, get_arq_pool
from app.schemas import PipelineAction, JobResponse, JobStatus, LogEntry, JobLogsResponse

router = APIRouter(tags=["pipeline"])

JOB_KEY_PREFIX = "granola:job:"
LOG_KEY_PREFIX = "granola:job:"


@router.post("/pipeline/{action}", response_model=JobResponse)
async def trigger_pipeline(action: PipelineAction):
    redis = await get_redis()
    arq = await get_arq_pool()

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    job_data = {
        "job_id": job_id,
        "status": JobStatus.queued.value,
        "action": action.value,
        "created_at": now,
        "result": None,
        "started_at": None,
        "completed_at": None,
        "duration_seconds": None,
        "items_processed": None,
        "items_total": None,
        "error_count": 0,
        "current_step": None,
        "steps_completed": [],
    }
    await redis.set(
        f"{JOB_KEY_PREFIX}{job_id}",
        json.dumps(job_data),
        ex=86400,
    )

    # Add to recent jobs list
    await redis.lpush("granola:recent_jobs", job_id)
    await redis.ltrim("granola:recent_jobs", 0, 49)

    # Enqueue ARQ job
    task_name = f"task_{action.value}"
    await arq.enqueue_job(task_name, _job_id=job_id)

    return JobResponse(**job_data)


@router.get("/pipeline/jobs", response_model=list[JobResponse])
async def list_jobs():
    redis = await get_redis()
    job_ids = await redis.lrange("granola:recent_jobs", 0, 19)

    jobs = []
    for jid in job_ids:
        raw = await redis.get(f"{JOB_KEY_PREFIX}{jid}")
        if raw:
            jobs.append(JobResponse(**json.loads(raw)))

    return jobs


@router.get("/pipeline/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    redis = await get_redis()
    raw = await redis.get(f"{JOB_KEY_PREFIX}{job_id}")

    if not raw:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(**json.loads(raw))


@router.get("/pipeline/jobs/{job_id}/logs", response_model=JobLogsResponse)
async def get_job_logs(
    job_id: str,
    after: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
):
    redis = await get_redis()

    # Verify job exists
    raw = await redis.get(f"{JOB_KEY_PREFIX}{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Job not found")

    log_key = f"{LOG_KEY_PREFIX}{job_id}:logs"
    total = await redis.llen(log_key)

    raw_entries = await redis.lrange(log_key, after, after + limit - 1)
    logs = [LogEntry(**json.loads(entry)) for entry in raw_entries]

    has_more = (after + len(logs)) < total

    return JobLogsResponse(logs=logs, total=total, has_more=has_more)
