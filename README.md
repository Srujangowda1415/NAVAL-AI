# Naval Vessel Detection & Classification System

AI system for detecting ships in images/video, classifying vessel type, and
scoring hazard level (Safe / Suspicious / Hazardous / Unknown), with a REST
API backend, a Next.js dashboard, and a Postgres-backed detection history.

## Status: Phase 1 — backend core scaffold (in progress)

This repo is being built in phases, each fully functional before moving to
the next:

| Phase | Scope | Status |
|---|---|---|
| 1 | Backend scaffold: FastAPI app, config, DB models, hazard rule engine, YOLO wrapper, `/upload-image` | ✅ done |
| 2 | Dataset prep (download/merge/clean → YOLO format), training scripts (cloud-GPU tuned), evaluation | ✅ done |
| 3 | Video pipeline (tracking → annotated rebuild), PDF reports, annotated-image rendering | ✅ done |
| 4 | Next.js frontend (dashboard, upload, history, reports, settings, about) | ✅ done |
| 4.5 | Async video processing (background worker + job status) — fixes the blocking-request issue flagged after Phase 3 | ✅ done |

## Phase 2 — dataset prep + training (cloud GPU)

Everything lives in `backend/training/`:

- `download_datasets.py` — automates what the Kaggle API allows (SeaShips pointer, Kaggle ship datasets, Airbus Ship Detection competition data), and prints exact manual steps for the datasets that require a request form or registration (HRSC2016, DOTA, Singapore Maritime).
- `dataset_utils.py` — shared normalization: maps messy source class names to our 20 canonical classes (see `CLASS_NAME_ALIASES`), converts Pascal-VOC boxes to YOLO format, de-dupes images by content hash, splits into train/valid/test.
- `prepare_dataset.py` — walks `datasets/raw/*`, converts VOC-XML-annotated datasets to YOLO format, merges, dedupes, splits. Unrecognized class labels are skipped (never silently mislabeled) and logged so you can add an alias.
- `augment_weather.py` — synthesizes fog/rain/snow/night/haze+glare variants of the training split using Albumentations, with matching YOLO labels copied over unchanged (pixel-level transforms only, so boxes stay valid — verified against a test image). Only touches `train/`, never `valid/test`, so evaluation stays honest. This exists because **no single public dataset covers your full 20-class taxonomy across all weather conditions** — see the notes in `download_datasets.py` for what real weather-diverse maritime datasets exist (WSODD, SeaDronesSee, Singapore Maritime) and their real limitations (Baidu-only hosting, registration walls, or narrow object taxonomies).
- `train.py` — fine-tunes YOLO11 on a single cloud GPU: AMP on, cosine LR, early stopping, checkpoints every 10 epochs (so a Colab disconnect doesn't lose the run), ship-appropriate augmentation (water/sky lighting jitter, some vertical-flip probability for aerial shots), auto-copies `best.pt` to `models/weights/` where the backend already expects it. Also supports `--resume`, `--evaluate-only`, `--export-only` (ONNX).
- `colab_train.ipynb` — ready-to-run notebook: mounts Drive for persistence across disconnects, installs deps, runs the full pipeline end to end.

```bash
# On your cloud GPU instance (or open colab_train.ipynb in Colab):
cd backend/training
python download_datasets.py --target ../../datasets/raw
# ...grab HRSC2016/DOTA/Singapore Maritime manually per the printed instructions...
python prepare_dataset.py --raw-dir ../../datasets/raw --out-dir ../../datasets
python augment_weather.py --dataset-dir ../../datasets --variants-per-image 2
python train.py --data ../../datasets/naval_dataset.yaml --epochs 150 --batch 16
```

`best.pt` lands at `models/weights/best.pt` — exactly where `backend/inference/detector.py` already looks, so `/upload-image` goes live with zero config changes once training finishes.

## Folder structure

```
naval-ai/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/
│   │   └── config.py             # env-driven settings (single source of truth)
│   ├── config/
│   │   └── hazard_rules.yaml     # hazard policy — edit here, not in code
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── upload.py         # /upload-image (live), /upload-video (stub)
│   │   │   └── history.py        # /history, /report/{id}, DELETE /history/{id}
│   │   └── schemas/
│   │       └── detection.py      # Pydantic request/response models
│   ├── inference/
│   │   ├── detector.py           # YOLO wrapper (image + video/tracking)
│   │   └── hazard_classifier.py  # reads hazard_rules.yaml, rule-based today,
│   │                              #   swappable for an ML model later
│   ├── database/
│   │   ├── session.py            # SQLAlchemy engine/session
│   │   └── models.py             # DetectionJob, ShipDetection tables
│   ├── training/                 # (Phase 2) training scripts
│   ├── uploads/ outputs/ reports/  # runtime storage (gitignored)
│   └── tests/
├── frontend/                     # (Phase 4) Next.js app
├── datasets/
│   ├── naval_dataset.yaml        # YOLO dataset config, 20 ship classes
│   └── train/valid/test/{images,labels}/
├── models/weights/                # trained .pt files go here
├── docs/
└── docker-compose.yml             # Postgres now; backend/frontend services stubbed
```

## Running the backend now

```bash
cd naval-ai/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# start Postgres
cd .. && docker compose up -d postgres

cd backend
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

**Note:** `/upload-image` will run end-to-end once a trained model exists at
`YOLO_WEIGHTS_PATH` (default `models/weights/best.pt`). Until then, `/health`
reports `model_loaded: false` and detection calls return a clear error rather
than failing silently — that's expected until Phase 2 (training) is done.

## Design decisions worth knowing

- **Hazard levels are config, not code.** `backend/config/hazard_rules.yaml`
  maps each ship class to a hazard level. `HazardClassifier` just reads and
  applies it. Swapping in an ML-based hazard model later means replacing the
  `classify()` implementation — no caller changes.
- **Detector is lazy about weights.** The API boots even without a trained
  model so you can develop the rest of the stack in parallel with training.
- **DB uses SQLAlchemy models now, Alembic migrations for production.** The
  `create_all()` call in `main.py` is dev-only.

## Phase 3 — video pipeline, annotated rendering, PDF reports

- `inference/annotator.py` — draws bounding boxes + `class / confidence / [HAZARD]` labels, color-coded per hazard level (green=safe, amber=suspicious, red=hazardous, gray=unknown). Used for both single images and every video frame. **Visually verified** against a synthetic test image.
- `inference/video_processor.py` — runs `Detector.predict_video_stream` (ByteTrack/BoT-SORT), annotates every frame, rebuilds an annotated `.mp4`, and collapses per-frame detections into one summary row per *tracked ship* (not per frame) — so a ship visible in 400 frames shows up once in the report, with its highest-confidence classification. Enforces `MAX_VIDEO_DURATION_SECONDS`.
- `reports/generator.py` — generates a styled PDF (navy/steel-blue theme matching the planned UI) with summary stats, the annotated image, and a hazard-color-coded per-ship table. **Rendered and visually verified** — see below.
- `/upload-image` and `/upload-video` now both return a real `annotated_output_url` (served via `/outputs/...`, mounted as static files in `main.py`).
- `/report/{id}` generates the PDF on first request and caches it at `reports/job_{id}_report.pdf`, served via `/reports/...`.

## Phase 4 — Next.js frontend

`frontend/` is a real, verified Next.js 16 (App Router) + TypeScript +
Tailwind CSS 4 app — not a mockup:

- **7 pages**: `/` (landing), `/dashboard`, `/upload`, `/history`, `/reports`, `/settings`, `/about`
- **Design**: dark navy/steel-blue "tactical console" theme per spec, with a signature bracket-cornered panel motif (`.bracket-panel`) fitting a detection/targeting system, Rajdhani/Inter/JetBrains Mono type system, and hazard colors that match `hazard_rules.yaml` and the PDF report exactly
- **`/upload`**: drag-and-drop for image or video, shows the annotated output, per-ship table, and a PDF report link — wired directly to `/upload-image` and `/upload-video`
- **`/dashboard`**: aggregate stats + a recharts bar chart of ships-per-upload, computed client-side from `/history`
- **`/history`**: full table with delete and report-download actions
- **`/settings`**: live backend health check (`/health`) so you can see at a glance whether a model is trained/loaded

**Verified, not just written**: `npx tsc --noEmit` and `npx eslint .` both pass clean, and a full `next build` (with fallback fonts, since this sandbox can't reach fonts.googleapis.com) successfully compiled and statically prerendered all 8 routes. Swap back to `npm run dev`/`npm run build` as normal in an environment with internet access — nothing else changes.

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm run dev
```

## Phase 4.5 — async video processing (bug fix)

**Problem:** `/upload-video` ran the whole pipeline synchronously inside the request — a multi-minute video meant a multi-minute HTTP request, tying up an API worker thread and leaving the browser hanging.

**Fix:** video jobs now go through a real background queue:

- `core/queue.py` — Redis connection + RQ queue
- `worker.py` — separate process that pulls jobs off the queue and runs them (scale horizontally with more worker processes/containers)
- `inference/tasks.py` — the actual background task; updates the job's `status` (`pending` → `processing` → `completed`/`failed`) and records `error_message` on failure instead of losing the job
- `/upload-video` now returns **202 Accepted** immediately with the job id; poll `GET /jobs/{id}` for progress and final results
- Frontend (`/upload`, `/history`) updated to poll and show live status (queued/processing spinners) instead of blocking

**Verified end-to-end with a real Redis instance and a real separate worker process** (not mocked): confirmed the job actually sits in the Redis queue after enqueue, confirmed a worker process picks it up and updates job status in the database, and confirmed via FastAPI's TestClient that `/upload-video` now returns in **0.018s** instead of blocking for the full processing duration.

Images are unaffected — they're fast enough to stay synchronous.

## Next step

Phase 5: Dockerfiles for backend/worker/frontend, wiring up the
already-stubbed `docker-compose.yml` services, a deployment guide, and
multi-user auth/RBAC.
