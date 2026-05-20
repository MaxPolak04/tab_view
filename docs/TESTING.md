# Quality Assurance & Code Quality Gates

TabView implements a multi-layered quality assurance strategy that spans from local unit verification to automated cloud-native security orchestration. This ensures regression boundaries, code formatting predictability, and absolute package dependency auditing.

---

## 1. Test Suite Matrix

The core test suite is built on top of the `pytest` framework and lives entirely inside the `/tests` directory. The test components utilize specialized shared context fixtures configured within `conftest.py`.

### Architectural Test Categories

- **Unit Tests (`tests/test_models/` & `tests/test_utils/`):** Evaluate isolated behavioral logic across system models (e.g., `test_device.py`, `test_event.py`) and standard helper modules (e.g., `test_detect_type.py`, `test_str_to_bool.py`).
- **Integration Tests (`tests/test_views/`):** Validate request-response network life cycles, multi-device routing parameters, application context middleware states, and transactional API endpoint behavior (covering authentication layers, device queues, media controllers, and scheduling matrices).

### Native Test Execution

To run the entire suite locally within your current virtual execution context, run:

```bash
uv run pytest
```

### Coverage Metrics Reporting

To analyze line-by-line test execution depth and isolate untested execution paths, generate a coverage calculation report:

```bash
pytest --cov
```

---

## 2. Shift-Left Security & Pre-Commit Quality Gates

Code styling rules, static quality patterns, and security guardrails are checked directly on the engineering workspace before modifications enter the remote git tree.

The project configures automated validation boundaries using `.pre-commit-config.yaml`:

- **Operational Linting & Refactoring (`Ruff`):** Enforces immediate compliance with PEP 8 standards, structural formats, and layout properties.
- **Static Application Security Testing (`Bandit`):** Evaluates Python source trees dynamically to prevent high-risk code bugs, hardcoded cryptographic payloads, or debugging anomalies.
- **Structural Sanity Hooks:** Checks trailing whitespace states, enforces standard POSIX line endings, and protects the git architecture tree from accidental binary blobs.

To manually trigger the pre-commit gate validation checks against all project files simultaneously without performing a git commit, execute:

```bash
pre-commit run --all-files
```

---

## 3. Automated CI/CD Pipelines (GitHub Actions)

Every pull request or merge operation targeting the primary distribution branches executes an integrated, automated continuous verification pipeline specified in `.github/workflows/ci-cd.yml`.

The automation environment runs the following pipeline stages sequentially:

### Stage A: Code Quality, Styling & Dependency Audits

1. **Dockerfile Sanity Check (`Hadolint`):** Verifies the application container build scripts to ensure minimal layer overhead, proper privilege dropping, and optimal build patterns.
2. **Strict Linter Assessment (`Ruff check .`):** Rejects any code structure introducing unused definitions, formatting breaks, or logical design errors.
3. **Advanced SAST Skan (`Bandit`):** Scans the `tab_view/` module directory structure to prevent unsafe operations from merging into downstream deployments.
4. **Dependency Tree Supply Chain Auditing (`pip-audit`):** Interrogates package graphs dynamically to discover, report, and block any third-party libraries introducing known vulnerabilities (CVEs).

### Stage B: Execution of Testing Frameworks

1. Installs clean application dependencies from scratch inside the runner engine based on `uv.lock`.
2. Spins up an in-memory test matrix to run all `pytest` operations inside an isolated containerized environment.

### Stage C: Container Security Vulnerability Assessments (`Trivy`)

Before building and pushing production images to Docker Hub or GitHub Packages (GHCR), the pipeline assembles a test image asset and evaluates it using `Trivy`:

- Analyzes the base Linux distribution image profile layer by layer.
- Scans system packages and internal package graphs for hidden software defects.
- **Exit Code Guardrail:** If an image scanning run encounters any security defect flagged as `HIGH` or `CRITICAL`, the scanning engine triggers an automatic pipeline exit sequence, immediately blocking build distribution actions to protect production targets.
