# Deployment Guide

## Local (Docker Compose)

```bash
cp backend/.env.example backend/.env
# edit backend/.env: set a real JWT_SECRET_KEY at minimum
#   python -c "import secrets; print(secrets.token_hex(32))"

docker compose up --build
```

This starts: `postgres`, `redis`, `backend` (FastAPI on :8000), `worker`
(video processing), `frontend` (Next.js on :3000).

First run: visit `http://localhost:3000`, check **Settings** to confirm
the backend is reachable, then register an account — **the first
registered user automatically becomes admin**.

Scale workers for parallel video processing:

```bash
docker compose up --scale worker=3
```

## Verified in this environment

Since this sandbox has no `docker` binary, the Dockerfiles themselves
couldn't be `docker build`-tested directly here. What *was* verified:

- `docker-compose.yml` parses as valid YAML
- Every non-GPU dependency in `backend/requirements.txt` installs cleanly
  into a fresh venv with no version conflicts (torch/ultralytics excluded
  only because of this sandbox's disk size, not a known compatibility issue)
- `main.py` imports cleanly and all 14 API routes register correctly from
  that fresh install
- The full auth flow (register/login/RBAC enforcement/promotion) was
  tested end-to-end against a real FastAPI TestClient instance
- The async video pipeline (Phase 4.5) was tested end-to-end against a
  real Redis server and a real separate worker process

Run `docker compose up --build` yourself as the final confirmation step —
the Dockerfiles follow standard, low-risk patterns (`python:3.12-slim` +
pip install, multi-stage Next.js standalone build) but a from-scratch
`docker build` is worth doing once before relying on this in production.

## GPU inference in production

The default `backend/Dockerfile` is CPU-only (`python:3.12-slim`). For
GPU inference:

1. Swap the base image for an NVIDIA CUDA image matching your installed
   driver, e.g. `nvidia/cuda:12.4.1-runtime-ubuntu22.04`, then install
   Python 3.12 and the same `requirements.txt` on top of it.
2. Install the CUDA build of `torch`/`torchvision` (see
   https://pytorch.org/get-started/locally/ for the right index URL for
   your CUDA version) instead of the CPU wheels.
3. Set `YOLO_DEVICE=0` (or the relevant GPU index) in `.env`.
4. Add an NVIDIA runtime device reservation to the `backend` and `worker`
   services in `docker-compose.yml`, or pass `--gpus all` if running the
   container directly.

Training (`backend/training/train.py`) already assumes a cloud GPU — see
Phase 2 and `colab_train.ipynb`. Training and inference don't need to run
on the same machine: train once on a cloud GPU, download `best.pt`, and
serve it from a CPU (or cheaper GPU) instance in production if latency
allows.

## Environment variables that matter in production

| Variable | Why it matters |
|---|---|
| `JWT_SECRET_KEY` | **Must** be changed from the default — anyone with the default can forge tokens |
| `DATABASE_URL` | Point at a managed Postgres instance, not the compose container, for real deployments |
| `REDIS_URL` | Same — a managed Redis (or at least a persisted one) so queued jobs survive a restart |
| `ALLOWED_ORIGINS` | Set to your actual frontend origin(s); the default allows only `localhost:3000` |
| `YOLO_WEIGHTS_PATH` | Must point at a real trained `best.pt` — see Phase 2 |
| `MAX_VIDEO_DURATION_SECONDS` | Tune based on your worker capacity and users' patience |

## Auth / RBAC summary (Phase 5)

Three roles, least to most privileged: `viewer` < `analyst` < `admin`.

- `viewer`: read history, reports, job status
- `analyst`: viewer + upload images/videos, delete jobs
- `admin`: analyst + list/promote users (`GET /api/auth/users`,
  `PATCH /api/auth/users/{id}/role`)

The first account ever registered becomes `admin` automatically (nobody
else exists yet to promote them). Every registration after that defaults
to `viewer`.

Endpoints:

- `POST /api/auth/register` — email + password (min 8 chars) → account
- `POST /api/auth/login` — OAuth2 password flow → JWT (24h expiry by default)
- `GET /api/auth/me` — current user
- `GET /api/auth/users` (admin) — list all users
- `PATCH /api/auth/users/{id}/role` (admin) — promote/demote

## Still open after Phase 5

- No HTTPS termination configured — put this behind a reverse proxy
  (nginx, Caddy, or your cloud provider's load balancer) with TLS in any
  real deployment; don't expose ports 8000/3000 directly to the internet
- No rate limiting on `/auth/login` or `/upload-*`
- No automated Alembic migration workflow wired into Docker startup
  (`main.py`'s `create_all()` is dev-only, as noted in Phase 1)
- No log aggregation / monitoring / alerting
