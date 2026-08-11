FROM python:3.11-slim

# tesseract-ocr: required at the OS level for pytesseract (the Python package is
# just a wrapper around this binary). libpq-dev: for psycopg2 if you switch to Postgres.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

# ml/models/*.pkl ship inside the image (see ml/ folder) so fraud detection and
# forecasting work immediately — no training step required at deploy time.

ENV ENV=production \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# gunicorn with uvicorn workers: production-grade process management (auto-restart
# workers, graceful reload). --workers 2 is a sane default for a small deployment;
# bump it (roughly 2x CPU cores + 1) if you have more headroom.
CMD ["gunicorn", "main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
