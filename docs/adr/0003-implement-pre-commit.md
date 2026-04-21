# ADR 0003: Implementing pre-commit hooks for code quality and DevSecOps practices

**Date:** 21.04.2026
**Status:** Accepted

## 1. Context and Problem
As the TabView application (Flask, Docker, Nginx) grows, so does the risk of introducing formatting inconsistencies, syntax errors in configuration files, and potential security vulnerabilities (e.g., hardcoded secrets) into the repository. Relying solely on human vigilance during Code Review in a Git-Flow environment is insufficient, time-consuming, and error-prone.

To elevate the project's engineering standards, we needed a mechanism to automatically reject flawed code *before* it is permanently recorded in the Git history (at the commit phase).

## 2. Decision
We decided to adopt the **`pre-commit`** framework, managed via the `.pre-commit-config.yaml` file.

The selected toolset aligns with DevOps (automation, formatting) and DevSecOps (early vulnerability detection) principles. The following tools were integrated into the pipeline:

* **Standard File Filters:** `trailing-whitespace`, `end-of-file-fixer`, `check-added-large-files` – prevents repository bloat and maintains clean Git history.
* **Syntax Verification (YAML):** `check-yaml` – safeguards against infrastructure deployment failures caused by invalid indentation.
    * *Architectural Exception:* The `check-yaml` linter explicitly ignores `docker-compose*.yml` files (`exclude: ^docker-compose.*\.yml$`). The tool relies on a strict parser that does not recognize Docker Compose V2 specific tags (e.g., `!reset`), which previously caused false positives and blocked the CI/CD workflow.
* **Formatting and Linting (Python):** `ruff` and `ruff-format` – replaces legacy tools (like flake8 or black), offering drastically faster code analysis and enforcing a unified coding style across the team.
* **Security (SAST):** `bandit` – passive scanning of Python code for common security vulnerabilities (part of our DevSecOps strategy).

## 3. Consequences

### Positive:
* **Shift-Left Security:** Security and quality issues are caught immediately on the developer's local machine, rather than failing later in GitHub Actions or production.
* **Time Savings (Code Review):** Code Reviews can now focus strictly on business logic rather than debates over code style, spacing, or missing newlines.
* **Consistency:** Every team member (and future contributor) is structurally forced to write code adhering to the exact same standard.

### Negative / Constraints:
* **Local Overhead:** Requires developers to perform a one-time local setup (`pre-commit install`) upon cloning the repository.
* **Commit Duration:** The `git commit` command takes a few seconds longer due to the hook execution time.
* **Exception Management:** As demonstrated by the `check-yaml` issue, overly strict generic tools can block modern domain-specific solutions, requiring manual configuration of exclusion rules.
