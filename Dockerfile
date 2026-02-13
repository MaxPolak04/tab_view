# Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure stdout/stderr are sent straight to terminal (unbuffered)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Install system-level dependencies required for building Python packages and media handling
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 2. Install 'uv' using the official binary from the provided image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Set the application working directory
WORKDIR /app

# 4. Copy dependency files first to leverage Docker layer caching
# This ensures 'uv sync' is only re-run if dependencies actually change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 5. Copy the rest of the application source code
COPY . .

# Ensure the startup script is executable
RUN chmod +x run.sh

# --- SECURITY SECTION (NON-ROOT USER) ---

# 6. Create a dedicated system group and user to run the application
# Using a non-privileged user mitigates potential container breakout attacks
RUN addgroup --system appgroup && adduser --system --group appuser

# 7. Grant the new user ownership over the application directory
# Necessary for the user to read source files and write to the static/uploads directory
RUN chown -R appuser:appgroup /app

# Check every 30 seconds, wait a maximum of 3 seconds for a response,
# try 3 times before declaring failure.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# 8. Switch from 'root' to the restricted user
USER appuser

# ----------------------------------------

# 9. Update PATH to use the virtual environment created by 'uv'
ENV PATH="/app/.venv/bin:$PATH"

# 10. Expose the port the application listens on
EXPOSE 8000

# 11. Define the entry point for the container
CMD ["./run.sh"]
