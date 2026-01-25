FROM python:3.10-slim

WORKDIR /app

# Install system deps (needed for building some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps separately for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

EXPOSE 8000

# Gunicorn + Uvicorn workers (production)
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000"]
#convert it to multistage dockerfile with build stage and production stage