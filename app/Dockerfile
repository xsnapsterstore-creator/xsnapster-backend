# =========================
# 🏗️ Build stage
# =========================
FROM python:3.10-slim AS builder

WORKDIR /app

# System deps for building wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into wheels
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir -r requirements.txt -w /wheels


# =========================
# 🚀 Production stage
# =========================
FROM python:3.10-slim

WORKDIR /app

# Runtime deps only
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy app source
COPY . .

EXPOSE 8000

# Default = API
# Worker overrides this command in docker-compose
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000"]
