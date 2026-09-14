# ─────────────────────────────────────────────────────────────
# BigBell — Creator Success AI Platform
# Instant deployment:  docker build -t bigbell . && docker run -p 8501:8501 -v bigbell-data:/app/data bigbell
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Fail fast on missing build context files / broken deps
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Minimal system libs (chromadb needs libgomp for its native index)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first so this layer is cached across rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application (includes sample data in data/sample_data/)
COPY . .

# App entry point
EXPOSE 8501

# NOTE: Do NOT use VOLUME here — it masks the COPYed sample data.
# Mount a named volume at runtime if you want persistence:
#   docker run -v bigbell-data:/app/data ...

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5)"

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
