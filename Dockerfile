# Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Install system dependencies
# Curl is needed for HEALTHCHECK
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    ffmpeg \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set default timezone
ENV TZ=Europe/Warsaw

# 2. Install 'uv'
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Set working directory
WORKDIR /app

# 4. Install dependencies (Root does this, but we fix permissions later)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 5. Copy source code
COPY . .

# Ensure executable
RUN chmod +x run.sh

# --- SECURITY SECTION ---

# 6. Create user WITH HOME DIRECTORY using low-level tools (Safe & Standard)
# -r: system account
# -g appgroup: primary group
# -m: create home directory
# -d /home/appuser: specific home path
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -m -d /home/appuser appuser

# 7. Grant ownership to application files
# This fixes the ownership of .venv created by root in step 4
RUN chown -R appuser:appgroup /app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# 8. Switch user
USER appuser

# ----------------------

# 9. Set HOME and PATH
ENV HOME=/home/appuser
ENV PATH="/app/.venv/bin:$PATH"

# 10. Expose & Run
EXPOSE 8000
CMD ["./run.sh"]
