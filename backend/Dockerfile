# CPU-only image by default — see docs/DEPLOYMENT.md for the CUDA base
# image swap needed to run inference on a GPU host.
FROM python:3.12-slim

WORKDIR /app

# opencv needs these system libs even in "headless" mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Copy model weights (from repo root models/ directory into the container)
# The build context is set to repo root in render.yaml so this path resolves.
COPY models/weights/ ./models/weights/

RUN mkdir -p uploads outputs reports

EXPOSE 8000

# Default command runs the API. The `worker` service in docker-compose.yml
# overrides this with `python worker.py` — same image, different process.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
