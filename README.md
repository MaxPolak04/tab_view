# TabView System

![Project Version](https://img.shields.io/badge/version-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Flask](https://img.shields.io/badge/Flask-3.0-000000)
![Package Manager](https://img.shields.io/badge/uv-Fast-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![CI/CD](https://img.shields.io/badge/CI%2FCD-Passing-success)
![Security: Bandit](https://img.shields.io/badge/security-bandit-green.svg)
[![Security: Trivy](https://img.shields.io/badge/security-trivy-green.svg)](https://aquasecurity.github.io/trivy/)
![Linter: Ruff](https://img.shields.io/badge/linter-ruff-red.svg)
[![License](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey)](LICENSE)

## 📌 About the Project

**An end-to-end Digital Signage system engineered with a focus on Zero-Downtime architecture, Shift-Left security, and enterprise-grade deployment.**

**TabView** is a robust web platform created to centrally manage information tablets, solving the problem of manual room booking and visual communication for **eNStudios**. Delivered as a complete solution, it offers a self-sustaining display client capable of real-time scheduling updates and media rotation without page reloads.

### Key High-Level Features

- **Enterprise Audit Trail:** Comprehensive tracking of all administrative actions (IP, UserAgent, and Event logging) to ensure strict accountability.
- **Interactive Scheduling:** Real-time event and booking management powered by a customized `FullCalendar.io` interface, backed by atomic validation rules.
- **Automated Display Engine:** A lightweight, polling-driven frontend architecture optimized for low-resource tablets, ensuring consistent playback loops.
- **Hardware Agnostic Asset Distribution:** Support for simultaneous scheduling of static images, HTML layouts, and MP4 video queues with custom display intervals.

---

## 🚀 Quick Start

Ensure you have **Docker** and **Docker Compose** installed on your host system.

### 1. Launch the Environment

Clone the repository, configure your environment, and spin up the containerized architecture:

```bash
git clone https://github.com/your-org/tab-view.git
cd tab-view
cp .env.example .env
docker-compose up -d
```

### 2. Automated Initialization

The container entrypoint script (`run.sh`) automatically executes the full initialization pipeline:

- Applies all pending database migrations (`flask db upgrade`).
- Runs the database seeder (`tab_view/seed.py`) to generate sample layouts, devices, and core records.

### 3. Immediate Access

Once the containers are healthy, open your browser and navigate to `http://localhost:8080`. You can log in immediately using the auto-generated evaluation credentials:

- **Username / Login:** `admin`
- **Password:** `admin`

_(⚠️ Note: These credentials are automatically provisioned by the seeder for evaluation. For configuration and production provisioning, refer to the guides below)._

---

## 📚 Documentation Index

The system's technical details are broken down into dedicated manuals following industry standards:

1. **[Engineer's Manual](docs/DEVELOPMENT.md)** – Comprehensive local development setup, package management via `uv`, database seeds, and testing utilities.
2. **[Architecture & Design Decisions](docs/ARCHITECTURE.md)** – Deep dive into the custom display client, caching mechanisms, 4K canvas layout calculations, and polling implementations.
3. **[Quality Assurance & Testing](docs/TESTING.md)** – Test suite matrix, coverage metrics, and execution models using `pytest`.
4. **[SRE & Operations Guide](docs/DEPLOYMENT.md)** – Production architecture, Nginx reverse proxy optimizations, Gunicorn tuning, and Rootless Docker container security structures.

---

## 🛠️ Built With

- **Backend:** Flask, SQLAlchemy (ORM), Flask-Migrate, Flask-RESTful.
- **Frontend:** Vanilla JS (ES6+), Bootstrap 5, FullCalendar.io, Flatpickr.
- **Tooling:** `uv` (Fast Python dependency management), Ruff (Linter/Formatter).
- **Security & Pipeline:** Bandit (SAST), Trivy (Container Scanning), Git Pre-commit Hooks, GitHub Actions.

---

## 🧠 Engineering Reflection & Mindset

This project represents a transition from structural coding to professional software engineering. Developed independently, it implements industry-best practices to prove that scalable software requires deliberate design:

- **Engineering over Coding:** Focus was placed on architecture resilience, structural security, and predictable error boundaries over just "making it work".
- **Self-Education:** Explored and deployed modern ecosystems (like `uv` package management and Rootless containerization) entirely on the fly based on documentation analysis.
- **Conscious Tooling:** Utilized automation and AI strictly as reviewers and architectural mentors. Every single line of code in this repository has been manually verified, tested, and understood.

---

## 📫 Feedback & Contact

As a student and beginning engineer, I highly value professional code reviews and architectural feedback. Feel free to connect:

- **GitHub Issues:** Technical bug reports and feature requests.
- **LinkedIn:** [Maksymilian Polak](https://www.linkedin.com/in/maksymilian-polak)

---

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**. See the [LICENSE](LICENSE) file for details.
