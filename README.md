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

### ⚡ Why this project stands out?

- **Production-Ready Architecture:** Deployed utilizing `Gunicorn` and `Nginx` within a fully isolated Rootless Docker environment. Heavy background processing (such as automated log cleanup) is delegated to asynchronous jobs via `APScheduler`, ensuring the main WSGI thread is never blocked.
- **Built-in Resilience:** A custom "Smart Fallback System" guarantees that tablet screens never go black, gracefully handling network outages or empty event schedules by serving default media.
- **Hardened Security & DevSecOps:**
  - API defense mechanisms based on strict Rate Limiting (`Flask-Limiter` paired with `Redis`).
  - Automated CI/CD pipelines with built-in SAST vulnerability scanning (`Bandit`) and dependency tree auditing (`pip-audit`).
  - Enforced data integrity and robust CSRF protection at the view layer.
  - An Enterprise Audit Trail tracking all administrative CRUD operations (logging IP, UserAgent, and specific events).

---

## 📸 Interactive Previews

_Note: The following visuals demonstrate the core functionality of TabView._

<p align="center">
  <img src="docs/assets/display-demo.gif" width="48%" alt="Display View: Media Rotation & Widgets">
  <img src="docs/assets/dashboard-demo.gif" width="48%" alt="Dashboard: Drag & Drop Scheduling">
</p>

---

## 🚀 Quick Start

To get the project up and running locally, you can use the provided Docker Compose configuration (`docker-compose.yml`). Before starting, ensure your environment is properly set up:

1. **Environment Variables:** Copy the `.env.example` file to a new file named `.env` and fill in the required variables.
2. **Web Server Config:** Ensure the `nginx.conf` file is present in the main directory.
3. **Branding Assets:** Verify that the `branding/` directory contains the following image files:
   - `default.png`
   - `logo_black.png`
   - `logo_white.png`

Once the prerequisites are met, simply start the containerized environment:

```bash
docker-compose up -d
```

---

## 📖 Documentation

If you are interested in the technical details, you can explore our [deep tech dive into the architecture](docs/ARCHITECTURE.md), which covers our display engine logic, UI scaling, caching strategy, and security mechanisms. For instructions on local environment setup, configuration variables, and database migrations, refer to the [development guide](docs/DEVELOPMENT.md).

To learn about our testing processes and coverage reporting, check out the [testing manual](docs/TESTING.md). When you are ready to move beyond the local environment, the [deployment instructions](docs/DEPLOYMENT.md) will guide you through the production stack, Nginx setup, and Rootless Docker. Finally, if you'd like to get involved, please read our [contributing guide](.github/CONTRIBUTING.md) to understand our Git flow and PR processes.

---

## 👨‍💻 About the Author & Learning Journey

I am an aspiring Junior Developer, and **TabView** is a project I realized during my student internship at eNStudios.

**Context:**
The application was created in a **Client (IT Admin) – Contractor (Me)** relationship. The company needed a dedicated solution but lacked the budget for commercial software or a Senior Developer to guide me. I had to fill this gap independently.

**My Path and Challenges:**
As a one-person team, I had to step out of the programmer role and take full responsibility for the product:

- **Engineering over Coding:** I didn't focus just on making the code "work", but on making it secure, maintainable, and resilient (e.g., handling backups, predicting production edge-cases).
- **Self-Education:** I learned everything – from architecture to CI/CD – on the fly, researching user needs and verifying best practices in documentation and online resources.
- **Conscious AI Use:** Artificial Intelligence was my mentor and reviewer (suggesting DevSecOps implementation, among other things), but never the "manager". **I am not a "VibeCoder"** – I verified every AI suggestion, and ultimately, I know and understand every line of code in this repository.

This project proved to me that I can deliver a complete, secure, and deployable solution, even under the pressure of limited resources and lack of mentorship.

---

## 📫 Feedback & Contact

As a student and beginning software engineer, I have made every effort to ensure this project meets production standards and adheres to Best Practices. However, your feedback is incredibly valuable to me.

Feel free to reach out via:

- **GitHub Issues:** For technical bug reports.
- **LinkedIn:** [Professional contact & networking](https://www.linkedin.com/in/maksymilian-polak)

---

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.
See the [LICENSE](LICENSE) file for details.
