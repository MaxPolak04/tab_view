# ADR 0002: Migration from pip to uv for Package and Environment Management

**Date:** 17.04.2026
**Status:** Accepted

## Context
During the early stages of development, TabView was a small project using standard `pip` and `requirements.txt`. As the application grew unexpectedly in scale, dependency count, and CI/CD complexity, the legacy solution became insufficient. We encountered performance bottlenecks (slow package installation in containers) and "it works on my machine" issues due to a lack of full determinism in dependency resolution.

## Decision
I decided to migrate from `pip` to **uv** (developed by Astral). `uv` serves as a unified replacement for multiple tools: package manager, Python version manager, and lockfile generator.

Key reasons for the migration:
1. **Performance:** Written in Rust, `uv` is significantly faster than `pip`, drastically reducing Docker build times and GitHub Actions execution duration.
2. **uv.lock File:** Implementing a deterministic lockfile eliminates environment drift, ensuring that every environment (Local, CI, Production) uses identical library versions.
3. **Flexibility:** `uv` allows for seamless Python interpreter management without requiring manual system-level installations.
4. **Modern Standards:** It is rapidly becoming the new standard in the Python ecosystem, merging the best features of `pip`, `poetry`, and `pyenv`.

## Consequences

### Positive:
* **Determinism:** Full installation reproducibility thanks to `uv.lock`.
* **Efficiency:** 30-50% reduction in CI/CD pipeline duration.
* **Simplification:** A single `pyproject.toml` file manages project metadata and tool configurations (Ruff, Pytest).
* **Reliability:** Better handling of complex dependency conflicts compared to legacy pip.

### Negative:
* **New Dependency:** `uv` must be installed on developer machines and included in the Docker base image (via the `COPY --from=ghcr.io/astral-sh/uv...` layer).
* **Learning Curve:** Team members must transition from `pip install` habits to `uv sync` or `uv add` workflows.

## Usage Examples
Installing dependencies in a container:
```bash
uv sync --frozen --no-dev
```
Adding a new package:
```bash
uv add [package_name]
```
