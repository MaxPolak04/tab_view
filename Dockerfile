FROM python:3.12-slim

# Enforce consistent Python behavior and prepare paths
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Warsaw \
    PATH="/app/.venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    ffmpeg \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Inject high-performance package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create a non-root system user for security isolation
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -m -d /home/appuser appuser

WORKDIR /app

# Copy dependency definitions and assign ownership immediately
# Prevents creating duplicate layers with chown later
COPY --chown=appuser:appgroup pyproject.toml uv.lock ./

# Drop root privileges early
USER appuser

# Install dependencies into /app/.venv
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source code
COPY --chown=appuser:appgroup . .

# Ensure entrypoint is executable
RUN chmod +x run.sh

# Verify application availability
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000
CMD ["./run.sh"]
