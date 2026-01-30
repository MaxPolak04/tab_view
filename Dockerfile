FROM python:3.12-slim

# 2. Installation of system dependencies (e.g., for MySQL client or media support)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. UV installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 4. Setting the working directory
WORKDIR /app

# 5. Copying configuration files and installing dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 6. Copying application code
COPY . .

# 7. Setting an environment variable so that Python can see the venv created by uv
ENV PATH="/app/.venv/bin:$PATH"

# 8. Opening port 8000 (standard for Gunicorn)
EXPOSE 8000

# 9. Starting Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]