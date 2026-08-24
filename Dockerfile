FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies for wheels
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libssl-dev \
    libffi-dev \
    python3-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy and build wheels to cache compiled packages
COPY requirements.txt /app/
# Increase pip timeout and retry wheel building to mitigate transient network failures
ENV PIP_DEFAULT_TIMEOUT=120
RUN pip install --upgrade pip setuptools wheel \
 && (for i in 1 2 3; do pip wheel --wheel-dir=/wheels -r requirements.txt && break || echo "pip wheel failed, retrying ($i)" && sleep 10; done)


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime dependencies (minimal)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    gosu \
 && rm -rf /var/lib/apt/lists/*

# Install from prebuilt wheels to avoid compiling in final image
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copy application code
COPY . /app

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh || true

# Create the application user. The entrypoint drops privileges after preparing mounted volumes.
RUN adduser --disabled-password --gecos "" webuser || true

ENV PORT=8000 \
    DJANGO_SETTINGS_MODULE=config.settings_production \
    APP_ENV=production \
    ENABLE_SWAGGER=False

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--workers", "3", "--bind", "0.0.0.0:8000"]
