# ADR 0001: Implementation of Automated Quality Gates and Shift-Left Security in the CI/CD Pipeline

**Date:** 17.04.2025
**Status:** Accepted

## Context
TabView is a web application designed to manage a fleet of digital screens. As a solo project, it lacks a natural "Code Review" phase typically conducted by a second engineer. At the same time, the application must meet production standards, be free of common vulnerabilities (CVEs), and ensure operational stability. Relying on a traditional manual testing process is insufficient and does not scale.

## Decision
I decided to implement a CI/CD architecture based on **GitHub Actions** combined with the **GitHub Flow** model (working on feature branches with a mandatory Pull Request approval process before merging into the main branch).

Additionally, to compensate for the lack of manual Code Reviews, the pipeline has been fortified with automated quality gates in accordance with the *Shift-Left Security* philosophy (detecting and resolving issues at the earliest possible stage of development).

The following tool stack has been implemented:
1. **Ruff:** For lightning-fast static analysis (SAST) and Python code formatting.
2. **Bandit & pip-audit:** For detecting security flaws in the source code and identifying known vulnerabilities in dependencies pulled from PyPI.
3. **Hadolint:** For enforcing best practices in `Dockerfile` configurations (e.g., mandating layer optimization and strict user permission verification).
4. **Trivy:** For scanning built container images (Debian/Alpine base OS) for system-level security vulnerabilities.

## Consequences

### Positive:
* **Automated Protection:** Code that fails to meet formatting standards or contains critical vulnerabilities has no technical possibility of being merged into the `main` branch.
* **Rapid Feedback Loop:** Errors are detected within minutes of pushing a branch to the remote repository, significantly shortening the remediation cycle.
* **High Deployment Confidence:** The `main` branch remains in a consistently stable state, ready for secure image building and publishing at any time (Always Deployable).

### Negative (Costs & Overhead):
* **Maintenance Complexity:** Additional tools in the pipeline (Trivy, Hadolint) require the active management of false-positives and configuring exceptions for unavoidable system-level issues (e.g., missing security patches at the Debian upstream level), which demands occasional manual intervention in configuration files.
* **Increased Build Time:** Introducing the intermediary step of building a local image and scanning it with Trivy during the Pull Request phase extends the overall pipeline execution time.
