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

**TabView** is an enterprise-grade web platform created to centrally manage information tablets, solving the problem of manual room booking and visual communication for **eNStudios**.

Delivered end-to-end, it offers a robust, autonomous display client capable of real-time scheduling updates and media rotation without page reloads.

### Key High-Level Features
* **Enterprise Audit Trail:** Comprehensive tracking of all administrative actions (IP, UserAgent, and Event logging) to ensure system integrity and accountability.
* **Interactive Scheduling:** Real-time media display queue management via a Drag & Drop `FullCalendar.io` interface.
* **Automated Display Client:** A self-sustaining, resilient frontend client for tablets that guarantees continuous operation via a Smart Fallback System.

---

## 📸 Interactive Previews

*Note: The following visuals demonstrate the core functionality of TabView.*

<p align="center">
  <img src="docs/assets/display-demo.gif" width="48%" alt="Display View: Media Rotation & Widgets">
  <img src="docs/assets/dashboard-demo.gif" width="48%" alt="Dashboard: Drag & Drop Scheduling">
</p>

---

## 🚀 Quick Start (TL;DR)

Get the project up and running locally in seconds using `uv` and Docker:

```bash
# 1. Install dependencies
uv sync

# 2. Start the containerized environment
docker-compose up -d
```

---

## 📖 Documentation Index

For deep dives into the technical configuration and architecture, please refer to the following manuals:

* [**Engineer's Manual** (`docs/DEVELOPMENT.md`)](docs/DEVELOPMENT.md) - Local setup, environment variables, database migrations, and seeding.
* [**Deep Tech Dive** (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md) - Display engine logic, 4K UI scaling, caching, and security mechanisms.
* [**Quality Assurance** (`docs/TESTING.md`)](docs/TESTING.md) - Test suite execution and coverage reporting.
* [**SRE & Operations** (`docs/DEPLOYMENT.md`)](docs/DEPLOYMENT.md) - Production stack, Rootless Docker, and Nginx configurations.
* [**Contributing Guide** (`.github/CONTRIBUTING.md`)](.github/CONTRIBUTING.md) - Git flow, pre-commit hooks, and PR processes.

---

## 👨‍💻 About the Author & Learning Journey

I am an aspiring Junior Developer, and **TabView** is a project I realized during my student internship at eNStudios.

**Context:**
The application was created in a **Client (IT Admin) – Contractor (Me)** relationship. The company needed a dedicated solution but lacked the budget for commercial software or a Senior Developer to guide me. I had to fill this gap independently.

**My Path and Challenges:**
As a one-person team, I had to step out of the programmer role and take full responsibility for the product:
* **Engineering over Coding:** I didn't focus just on making the code "work", but on making it secure, maintainable, and resilient (e.g., handling backups, predicting production edge-cases).
* **Self-Education:** I learned everything – from architecture to CI/CD – on the fly, researching user needs and verifying best practices in documentation and online resources.
* **Conscious AI Use:** Artificial Intelligence was my mentor and reviewer (suggesting DevSecOps implementation, among other things), but never the "manager". **I am not a "VibeCoder"** – I verified every AI suggestion, and ultimately, I know and understand every line of code in this repository.

This project proved to me that I can deliver a complete, secure, and deployable solution, even under the pressure of limited resources and lack of mentorship.

---

## 📫 Feedback & Contact

As a student and beginning software engineer, I have made every effort to ensure this project meets production standards and adheres to Best Practices. However, your feedback is incredibly valuable to me.

Feel free to reach out via:
* **GitHub Issues:** For technical bug reports.
* **LinkedIn:** [Professional contact & networking](https://www.linkedin.com/in/maksymilian-polak)

---

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.
See the [LICENSE](LICENSE) file for details.
