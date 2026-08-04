# ── Stage 1: Frontend Builder ──────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /build/frontend

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline 2>/dev/null || npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# Verify output
RUN ls -la out/index.html


# ── Stage 2: Production Runtime ────────────────────────────────────────────
FROM python:3.11-slim

# System dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ /app/backend/

# Copy frontend static build from Stage 1
COPY --from=builder /build/frontend/out /app/frontend/out

# Create storage directories
RUN mkdir -p /app/backend/storage/snapshots

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/zones')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
