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

LABEL maintainer="Virtual Fence Team"
LABEL version="1.0.0"
LABEL description="Enterprise Autonomous Perimeter Intrusion System"

# System dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -U appuser

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ /app/backend/

# Copy frontend static build from Stage 1
COPY --from=builder /build/frontend/out /app/frontend/out

# Create storage directories and set permissions
RUN mkdir -p /app/backend/storage/snapshots /app/backend/storage/videos \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Improved Health check using the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
