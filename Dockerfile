# syntax=docker/dockerfile:1
FROM python:3.11-slim

# ---- Metadata ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Set default "MODE" arg. Easily overwritten in specific docker-compose.yml instance
ARG MODE=api

# ---- System deps needed for some wheels (keep minimal) ----
# ---- Includes minimal system deps for headless Chromium ----
# If you need deps for specific packages are needed then add them here.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---- Copy only requirements first to leverage Docker layer cache ----
COPY requirements.txt .
COPY requirements-api.txt .

# Install dependencies at image build time (makes CLI fast).
# If requirements change, this layer will rebuild.
RUN pip install --root-user-action=ignore -r requirements.txt

# Conditionally install API dependency packages if MODE is "api"
RUN if [ "$MODE" = "api" ]; then \
      pip install --root-user-action=ignore -r requirements-api.txt; \
    fi

# ---- Copy application files ----
COPY . .

# ---- Add entrypoint script ----
RUN chmod +x /app/entrypoint.sh

# Default environment variables (can be overridden)
ENV MODE=api \
    API_FORCE_INSTALL=false \
    API_AUTO_START=true \
    TZ=UTC

# Entrypoint script will examine MODE and behave accordingly
ENTRYPOINT ["/app/entrypoint.sh"]