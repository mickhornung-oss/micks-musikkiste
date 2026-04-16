# Micks Musikkiste — Backend API
# Runs in mock engine mode by default (no ComfyUI/ACE-Step required)
#
# Build:  docker build -t micks-musikkiste .
# Run:    docker run -p 8000:8000 -e DATABASE_URL=postgresql+asyncpg://... micks-musikkiste

FROM python:3.11-slim

WORKDIR /app

# System deps (asyncpg needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

WORKDIR /app/backend

# Create required data directories
RUN mkdir -p data/outputs data/exports data/projects logs

ENV ENGINE_MODE=mock
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
