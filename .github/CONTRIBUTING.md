# Contributing to tab_view

First off, thank you for considering contributing to `tab_view`! It's people like you that make open-source and collaborative projects great.

This document outlines the process for setting up your development environment, our branching strategy, and how to submit your changes.



## 1. Development Environment Setup

We recommend running the Flask application and MySQL database locally for the fastest development feedback loop. Redis and Nginx are primarily used in the production Docker setup.

### Prerequisites
- Python 3.12+
- `uv` (Python package manager)
- Local MySQL server instance
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/maxpolak04/tab_view.git](https://github.com/maxpolak04/tab_view.git)
   cd tab_view
   ```

2. **Install dependencies using `uv`:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   Copy the example environment file and update the database credentials to match your local MySQL setup:
   ```bash
   cp .env.example .env
   ```

   Create a `.flaskenv` file in the root directory for local Flask development settings (this file is git-ignored):
   ```text
   FLASK_APP=tab_view
   FLASK_DEBUG=1
   ```

4. **Initialize the Database:**
   Ensure your local MySQL server is running and the database specified in your `.env` exists. Then, apply the migrations:
   ```bash
   uv run flask db upgrade
   ```

5. **Install Pre-commit Hooks:**
   We use `pre-commit` to ensure code quality (Ruff, Bandit, etc.) before every commit.
   ```bash
   uv run pre-commit install
   ```

6. **Run the application:**
   ```bash
   uv run flask run
   ```
   The application should now be available at `http://127.0.0.1:5000`.

## 2. Branching Strategy

We follow a simplified Git Flow model to keep our history clean and manageable:

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

## 3. Testing and Code Quality

Before submitting a Pull Request, ensure that your code passes all tests and linting checks.

- **Run tests locally:**
  ```bash
  uv run pytest
  ```
  *(Note: You can also use the built-in VSCode testing tab if you prefer a GUI).*

- **Pre-commit checks:**
  These will run automatically when you try to commit. If they modify files (like Ruff formatting), you will need to stage those files and commit again.

## 4. Submitting a Pull Request (PR)

1. Push your feature branch to GitHub.
2. Open a Pull Request against the **`develop`** branch (not `main`).
3. Provide a clear and descriptive title for your PR.
4. Wait for a code review and address any feedback.

Thank you for your contribution!
