# SRE & Operations

This document covers the production deployment mechanics, infrastructure configuration, and runtime security operations of TabView.

## Production Stack

The production environment is engineered for high availability and low latency, introducing structural changes compared to the local development workflow:

- **Application Server:** `Gunicorn` acts as the production WSGI server, replacing the native Flask development server. It is tuned with multiple workers to handle concurrent request streams efficiently.
- **Reverse Proxy & Static Files:** `Nginx` sits in front of Gunicorn as a reverse proxy. It terminates HTTP connections, handles SSL/TLS configurations, and directly serves static files (including user-uploaded media from the `uploads/` directory) to offload the Python backend and minimize response latency.

---

## Containerization & Environment Overrides

We utilize a multi-file Docker Compose architecture to cleanly separate configuration concerns and maintain environment parity:

- `docker-compose.yml`: Defines the base services infrastructure, multi-container network topographies, database persistence layers, and persistent volumes.
- `docker-compose.prod.yml`: The production override file. **This file strictly overwrites the base configuration**, integrating the production Nginx reverse proxy, adjusting container restart policies, and linking enterprise logging drivers to the host system's `journald`.

### ⚠️ Privilege Requirements & Container Engine Constraints

While the application layers are optimized for modern deployment, the network configuration imposes specific host-level constraints:

- **Privileged Port Binding:** Because `docker-compose.prod.yml` binds the environment to the standard HTTP **port 80** on the host machine, the container execution engine **requires root privileges** to allocate this privileged port.
- **Container Engine Compatibility:** Due to this strict requirement for host-level root authorization to bind low-numbered ports, **rootless container engines like Podman will fail to deploy this stack out-of-the-box** without advanced administrative sub-uid mapping or manual socket redirection. Standard Docker Daemon with root access is strictly required.

---

## 🎨 Enterprise Branding & Asset Configuration

To support client-specific customization and theme integration for eNStudios, the deployment stack relies on external branding assets loaded at runtime.

### Directory Placement & Structure

The deployment environment must include a dedicated `branding/` directory. **This directory must reside directly alongside the main `docker-compose.yml` configuration file** on the host filesystem root to ensure correct path mounting into the application context.

The directory must contain exactly three mandatory corporate graphic files with strict naming conventions:

1. `default.png` – The fallback background placeholder asset used across tablets when no active media queue is allocated.
2. `logo_black.png` – The dark variant corporate logo optimized for light layout mode interfaces.
3. `logo_white.png` – The light variant corporate logo optimized for dark layout mode interfaces.

Missing any of these components or misconfiguring the directory mount boundary will prevent branding layers from resolving correctly during server asset compilation.

---

## Rootless Docker Container Isolation (Runtime Security)

To adhere to strict DevSecOps and privilege minimization principles, the TabView application containers themselves are designed to run internally using an unprivileged `appuser`.

This creates a robust defense-in-depth security boundary: even though the host Docker daemon requires root access to initialize the stack and bind port 80, if an attacker manages to exploit an application-level vulnerability and achieve Remote Code Execution (RCE), they are strictly contained inside a sandboxed environment without root capabilities on the underlying host system.

---

## 🔐 Production Administrative Access & User Provisioning

When the production container environment boots up via `run.sh`, the initialization seeder generates a temporary administrator account for immediate setup verification.

⚠️ **CRITICAL SECURITY MANDATE:** Leaving the default evaluation credentials (`admin` / `admin`) active in a production environment accessible via port 80 constitutes a severe security risk. You must immediately rotate this password or provision a dedicated administrative account via the Flask Command Line Interface (CLI).

### Managing Users via the Flask CLI

Because the production containers execute under a restricted user context, any administrative command or manual user creation must be tunneled into the running container using `docker compose exec`.

Execute the following commands from the project root on the host server:

#### 1. Provision a New Secure Administrator:

To create a clean, dedicated admin account with a cryptographically secure password, run:

```bash
docker compose exec web flask create-user secure_admin P@ssw0rd123 --admin
```

#### 2. Rotate or Overwrite Existing Administrative Credentials:

If you need to replace or rotate credentials for an existing account via the CLI manager, execute:

```bash
docker compose exec web flask create-user admin NewHighlySecureP@ssw0rd! --admin
```

Once secure credentials are confirmed functional, ensure that any default or insecure testing profiles are completely audited and revoked from the system dashboard to preserve environment integrity.
