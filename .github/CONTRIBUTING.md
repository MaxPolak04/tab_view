# Contributing to TabView

First off, thank you for considering contributing to `TabView`! It's people like you that make open-source and collaborative projects great.

This document outlines our branching strategy, code quality standards, and the process for submitting your changes.

## 1. Development Environment Setup

We have moved all technical instructions regarding setting up the local environment, database migrations, and running the project to a dedicated manual.

👉 **Please refer to [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) to set up your local `uv` and Docker environment.**

_Crucial Step:_ Before making any commits, ensure you have installed the pre-commit hooks as instructed in the development guide (`pre-commit install`).

---

## 2. Branching Strategy & Release Lifecycle

We implement a simplified, stable Git branching topology focused on continuous delivery directly to the core production line:

- **`main`**: The primary production-ready and deployment-tracked branch. **Never commit or push directly to this branch.**
- **Feature Branches**: All isolated feature implementations, bug fixes, or documentation modifications must be developed on separate dedicated branches created directly from `main`. Use the naming convention `feature/your-feature-name` or `bugfix/issue-name`.

### Workflow Example:

```bash
git checkout main
git pull origin main
git checkout -b feature/awesome-new-calendar
# ... execute modifications and commit ...
git push origin feature/awesome-new-calendar
```

### Pull Request Rules & Code Consolidation

1. Open a Pull Request (PR) targeting the **`main`** branch.
2. Ensure that the automated GitHub Actions CI/CD pipelines pass successfully without breaking testing matrices, linters, or security scanners.
3. **Squash and Merge:** To maintain a clean, readable, and linear commit history, all accepted Pull Requests are merged exclusively using the **Squash and merge** strategy. This consolidates your entire feature development history into a single clean commit on the `main` branch.

### Release Automation Trigger

Once a Pull Request is successfully squashed and merged into `main`:

- You must provision a new version tag directly on the `main` head (adhering strictly to Semantic Versioning, e.g., `v1.0.1`).
- Create a formal **GitHub Release** from that specific tag. This process automatically triggers downstream deployment webhooks and pipeline steps to build and ship the release container assets.

---

## 3. Testing and Code Quality (Shift-Left)

Before submitting a Pull Request, you must ensure that your code adheres to our DevSecOps standards.

- **Run tests locally:**
  Every new feature or bugfix must be accompanied by relevant tests. Run the test suite using:

  ```bash
  uv run pytest
  ```

  _(Note: You can also use the built-in VSCode testing tab if you prefer a GUI)._

- **Pre-commit checks (Ruff & Bandit):**
  Our pre-commit hooks run automatically when you try to commit. If they modify files (like Ruff formatting) or block due to security issues (Bandit), you will need to fix the code, stage those files, and commit again.

---

## 4. Submitting a Pull Request (PR)

1. Push your feature branch to GitHub.
2. Open a Pull Request against the **`main`** branch.
3. Provide a clear and descriptive title for your PR detailing the problem solved.
4. Ensure the CI/CD pipeline (GitHub Actions) passes successfully.
5. Wait for a code review and address any engineering feedback.

Thank you for helping keep TabView secure, robust, and clean!
