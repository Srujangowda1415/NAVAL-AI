"""
Redis connection and RQ queue used to run video processing in the
background instead of blocking the upload request.

Why a queue instead of FastAPI BackgroundTasks: BackgroundTasks runs in
the same process as the web server, so a slow video still ties up an
API worker and doesn't survive a server restart. A real queue (RQ here,
backed by Redis) runs video jobs in a separate `worker.py` process,
keeps the API responsive, and lets you scale workers independently of
API instances in production (see docker-compose.yml).
"""

from __future__ import annotations

from redis import Redis
from rq import Queue

from core.config import settings

redis_conn = Redis.from_url(settings.redis_url)

# job_timeout is generous since video processing time scales with length;
# MAX_VIDEO_DURATION_SECONDS already caps how long a video can be, so this
# is just a safety net against a genuinely stuck job.
video_queue = Queue("video-processing", connection=redis_conn, default_timeout="30m")
