# Engineer's Manual

This document provides comprehensive technical instructions for setting up, configuring, and running the TabView development environment locally, both natively and using containerized workflows.

## Prerequisites

Before setting up the application, ensure that your local machine has the following dependencies installed:

- **Python:** Version 3.12 or higher
- **Package Manager:** `uv` (Fast Python package installer and resolver)
- **Database Server:** MySQL Server
- **Containerization:** Docker Engine & Docker Compose

---

## Environment Variables

The application relies on environment variables for system configuration. To set up your local environment, copy the template configuration file:

```bash
cp .env.example .env
```

Open the newly created `.env` file and configure the parameters according to your local setup. Below is a detailed reference of the available variables:

| Variable            | Type    | Default Value | Description                                                                                                      |
| ------------------- | ------- | ------------- | ---------------------------------------------------------------------------------------------------------------- |
| `FLASK_APP`         | String  | `tab_view`    | Defines the entry point of the application.                                                                      |
| `FLASK_DEBUG`       | Boolean | `1`           | Enables debug mode, hot-reloading, and interactive error tracking for local engineering.                         |
| `FLASK_SECRET_KEY`  | String  | _Required_    | A secure, randomly generated cryptographic key used for signing session cookies and form tokens.                 |
| `DATABASE_URL`      | String  | _Required_    | Database connection string following the RFC 1738 format (e.g., `mysql+pymysql://user:pass@localhost/tab_view`). |
| `WEATHER_LATITUDE`  | Float   | `52.4069`     | Geographic latitude used for the Open-Meteo API weather widget. Defaults to Poznań, Poland.                      |
| `WEATHER_LONGITUDE` | Float   | `16.9299`     | Geographic longitude used for the Open-Meteo API weather widget. Defaults to Poznań, Poland.                     |

---

## Database Management & Initialization

TabView automates database setup inside containerized environments, but also allows precise control during native development.

### 1. Containerized Automation (Docker Compose)

When deploying or running the application via Docker Compose (`docker-compose up -d`), the container lifecycle automatically executes the entrypoint script `run.sh`. This script orchestrates the entire database initialization transparently:

- Runs `flask db upgrade` to apply schema updates.
- Runs `uv run python -m tab_view.seed` to populate the environment with demo configurations, testing layouts, and devices.

### 2. Manual Native Execution

If you are developing natively on your host machine without Docker, you must trigger these steps manually in your terminal sequence:

```bash
# Apply migrations
uv run flask db upgrade

# Seed test data and initial records
python -m tab_view.seed
```

---

## 🔐 Initial Administrative Access

The database seeder script generates a default administrator account to allow immediate system evaluation and dashboard configuration.

Whether initialized automatically via Docker's `run.sh` or executed manually via the command line, use the following credentials for initial authentication:

- **Username / Login:** `admin`
- **Password:** `admin`

⚠️ **CRITICAL SECURITY REQUIREMENT:** These credentials are intended strictly for local evaluation and development environments. For production environments, immediately rotate this password or leverage the Flask CLI tool to provision a secure alternative user:

```bash
docker compose exec web flask create-user secure_admin P@ssw0rd123 --admin
```

---

## Dependency Management & Pipeline Fixes (uv)

When the CI/CD pipeline (e.g., `pip-audit`) blocks a PR due to vulnerable or outdated packages, use the following workflow to correctly upgrade dependencies, regenerate the lockfile, and sync your local environment.

### 1. Resolving Vulnerabilities & Updating Packages

To explicitly update a main dependency (writes to `pyproject.toml` and updates `uv.lock`):
```bash
uv add "package_name>=X.Y.Z"
```

To explicitly update a development dependency (e.g., `pip`, `pytest`):
```bash
uv add --dev "package_name>=X.Y.Z"
```

To update a transitive dependency (a package required by another package) directly in `uv.lock` without modifying `pyproject.toml` bounds:
```bash
uv lock --upgrade-package package_name
```

### 2. Synchronizing the Environment

After pulling changes from `main` or generating a new `uv.lock`, enforce synchronization with your local `.venv`:
```bash
uv sync
```

*Note: `uv sync` ensures your `.venv` is an exact mirror of `uv.lock`. Manual `pip install` modifications will be overwritten.*

### 3. Debugging Dependency Trees

If you need to investigate why a specific, vulnerable version is being installed:
```bash
uv tree
uv tree | grep package_name
```

---

## Local Execution (Native Workflow)

Once environment variables are verified and database migrations are applied to your local MySQL instance, launch the native Flask development server using `uv`:

```bash
uv run flask run
```

The application will initialize and start listening for local HTTP connections at `http://127.0.0.1:5000/`.

---

## Quality Gate & Pre-commit Hooks

To maintain clean architecture, strict code quality, and prevent vulnerable dependencies from being committed to the codebase, pre-commit hooks are strictly enforced via `.pre-commit-config.yaml`.

You must integrate these hooks into your local git lifecycle immediately after cloning the repository:

```bash
pre-commit install
```

Once installed, every execution of `git commit` automatically triggers verification pipelines executing:

- **`Ruff`**: For instantaneous linting and syntax formatting.
- **`Bandit`**: For static application security testing (SAST) targeting common Python vulnerabilities.
