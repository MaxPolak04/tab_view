# SRE & Operations

This document covers the production deployment mechanics of TabView.

## Production Stack

The production environment differs significantly from the local development setup:

- **Application Server:** `Gunicorn` acts as the production WSGI server instead of the native Flask development server.
- **Reverse Proxy & Static Files:** `Nginx` sits in front of Gunicorn. It terminates HTTP requests and directly handles serving static files (including user uploads from the `uploads/` directory), significantly improving latency and offloading the Python backend.

## Containerization Differences

We utilize two separate compose files to separate concerns:

- `docker-compose.yml`: Base configuration (network setup, database, volumes).
- `docker-compose.prod.yml`: The production override. It integrates Nginx, binds port 80 to the host, and links logging drivers to system `journald`.

## Rootless Docker & Isolation

By design, the TabView Docker containers run using an unprivileged `appuser` (Rootless configuration). This is a critical security measure—if an attacker manages to compromise the container, they do not gain root access to the underlying host system.

### Executing Commands in Production

Because of this architecture, administrative tasks must be executed via `docker compose exec`:

```bash
docker compose exec web flask create-user admin P@ssw0rd123 --admin
```
