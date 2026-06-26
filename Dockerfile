FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP="tab_view:create_app()" \
    FLASK_ENV=production \
    PORT=8000 \
    UV_SYSTEM_PYTHON=1 \
    VIRTUAL_ENV="/app/.venv"

ENV PATH="$VIRTUAL_ENV/bin:/root/.local/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl=7.88.1* \
    ca-certificates=20230311* \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

COPY pyproject.toml .

RUN uv lock && uv sync --frozen --no-dev --no-install-project

COPY . .

RUN uv sync --frozen --no-dev

RUN groupadd -r tabview && useradd -r -g tabview tabview \
    && mkdir -p /app/instance \
    && chown -R tabview:tabview /app

USER tabview

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "tab_view:create_app()"]
