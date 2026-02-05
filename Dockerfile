FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 2. Installation of system dependencies
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
# Kopiujemy najpierw pliki zależności, żeby Docker wykorzystał cache, jeśli kod się zmienił, a deps nie.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 6. Copying application code
COPY . .

# 7. Setting env so Python uses the venv
ENV PATH="/app/.venv/bin:$PATH"

# 8. Opening port
EXPOSE 8000

# 9. Starting Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]