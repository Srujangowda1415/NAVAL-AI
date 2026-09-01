# Root-level Dockerfile for Render deployment.
# Build context is the repo root so we can access both backend/ and models/.
FROM python:3.12-slim

WORKDIR /app

# opencv needs these system libs even in "headless" mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy model weights so the YOLO detector can load them at startup
COPY models/weights/ ./models/weights/

# Create runtime directories
RUN mkdir -p uploads outputs reports

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
