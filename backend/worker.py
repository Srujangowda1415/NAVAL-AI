"""
Background worker process for video jobs.

Run this alongside `uvicorn main:app` (separate process/container — see
docker-compose.yml's `worker` service). It pulls jobs off the
"video-processing" Redis queue and runs inference.tasks.process_video_job.

Usage:
    python worker.py

Scale horizontally by running more instances of this process — each one
pulls from the same queue, so N workers process N videos in parallel.
"""

from __future__ import annotations

import logging

from core.config import settings
from core.queue import redis_conn, video_queue

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


def main() -> None:
    from rq import Worker

    settings.ensure_directories()
    logger.info("Starting RQ worker on queue '%s' (%s)", video_queue.name, settings.redis_url)
    worker = Worker([video_queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
