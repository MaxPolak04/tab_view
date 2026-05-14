# Engineer's Manual

This document provides instructions for setting up the local development environment for TabView.

## Prerequisites

Ensure your system meets the following requirements before proceeding:

- **Python:** 3.12+
- **Package Manager:** `uv`
- **Database:** MySQL
- **Containers:** Docker Engine & Docker Compose

## Environment Variables

Copy `.env.example` to `.env`. Below is a breakdown of essential variables:

| Variable            | Description                                                   |
| ------------------- | ------------------------------------------------------------- |
| `FLASK_APP`         | Must be set to `tab_view`.                                    |
| `FLASK_DEBUG`       | Set to `1` for local development.                             |
| `FLASK_SECRET_KEY`  | Cryptographic key for session generation.                     |
| `DATABASE_URL`      | MySQL connection string.                                      |
| `WEATHER_LATITUDE`  | Latitude for Open-Meteo API (Defaults to Poznań: `52.4069`).  |
| `WEATHER_LONGITUDE` | Longitude for Open-Meteo API (Defaults to Poznań: `16.9299`). |

## Database Management

We use `Flask-Migrate` (Alembic) for schema versioning.

### Running Migrations

To apply the latest database schema updates, run:

```bash
uv run flask db upgrade
```

### Seeding Test Data

For a smooth development experience, populate the database with mock users, devices, and media using the built-in seeder:

```bash
python -m tab_view.seed
```

## Local Execution

To start the Flask development server natively using `uv`:

```bash
uv run flask run
```

## Pre-commit Hooks (Required)

To enforce Shift-Left security and code formatting standards (`Ruff` & `Bandit`), you must install the git hooks immediately after cloning the repository:

```bash
pre-commit install
```
