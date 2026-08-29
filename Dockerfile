FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first for layer caching
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install ".[aws,dev]"

COPY . .

# Default: run the ingestion script. Overridden per service in docker-compose.yml
CMD ["python", "scripts/ingest.py"]
