# Contributing to TabView

First off, thank you for considering contributing to `TabView`! It's people like you that make open-source and collaborative projects great.

This document outlines our branching strategy, code quality standards, and the process for submitting your changes.

## 1. Development Environment Setup

We have moved all technical instructions regarding setting up the local environment, database migrations, and running the project to a dedicated manual.

👉 **Please refer to [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) to set up your local `uv` and Docker environment.**

*Crucial Step:* Before making any commits, ensure you have installed the pre-commit hooks as instructed in the development guide (`pre-commit install`).

## 2. Branching Strategy

We follow a simplified Git Flow model to keep our history clean, secure, and manageable:

- **`main`**: The production-ready branch. **Never commit directly here.**
- **`develop`**: The main integration branch for the next release.
- **Feature Branches**: For new additions. Branch off from `develop` and name them `feature/your-feature-name`.
- **Hotfix Branches**: For urgent production bug fixes. Branch off from `main` and name them `hotfix/bug-name`.

### Workflow Example:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/awesome-new-calendar
# ... make your changes ...
git push origin feature/awesome-new-calendar
```

## 3. Testing and Code Quality (Shift-Left)

Before submitting a Pull Request, you must ensure that your code adheres to our DevSecOps standards.

- **Run tests locally:**
  Every new feature or bugfix must be accompanied by relevant tests. Run the test suite using:
  ```bash
  uv run pytest
  ```
  *(Note: You can also use the built-in VSCode testing tab if you prefer a GUI).*

- **Pre-commit checks (Ruff & Bandit):**
  Our pre-commit hooks run automatically when you try to commit. If they modify files (like Ruff formatting) or block due to security issues (Bandit), you will need to fix the code, stage those files, and commit again.

## 4. Submitting a Pull Request (PR)

1. Push your feature branch to GitHub.
2. Open a Pull Request against the **`develop`** branch (not `main`).
3. Provide a clear and descriptive title for your PR.
4. Ensure the CI/CD pipeline (GitHub Actions) passes successfully.
5. Wait for a code review and address any feedback.

Thank you for helping keep TabView secure and robust!
