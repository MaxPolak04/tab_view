# ADR 0004: Security architecture and selection of key libraries

**Date:** 21.04.2026
**Status:** Accepted

## 1. Context and Problem
Building the TabView web application as a solo developer means taking full responsibility for its security and data protection. Implementing defense mechanisms against common attack vectors (such as SQL Injection, Cross-Site Scripting (XSS), Cross-Site Request Forgery (CSRF), or Brute-force attacks) from scratch is highly risky, error-prone, and disproportionately time-consuming.

I needed a robust, battle-tested technology stack based on the Flask framework that is "Secure by Default," mitigating the most common vulnerabilities out of the box and allowing me to focus on business logic.

## 2. Decision
I decided to base the security and data management architecture on a specific set of dedicated, rigorously maintained libraries and extensions. Each is responsible for neutralizing specific threats:

* **python-dotenv:** *Security Goal:* Protection of secrets and configuration.
    *Application:* Ensures that encryption keys (e.g., `SECRET_KEY`), database passwords, and environment configurations are loaded from a local `.env` file and never committed to the source code or Git history.
* **Flask-SQLAlchemy:** *Security Goal:* Prevention of SQL Injection attacks.
    *Application:* Utilizing this Object-Relational Mapping (ORM) system ensures that all database queries are automatically parameterized, making it impossible to inject malicious SQL code.
* **Flask-WTF:** *Security Goal:* Protection against CSRF (Cross-Site Request Forgery).
    *Application:* Automatically generates and verifies cryptographic CSRF tokens for every submitted form, preventing attackers from executing unauthorized actions on behalf of an authenticated user.
* **Jinja2 (built into Flask):** *Security Goal:* Prevention of XSS (Cross-Site Scripting) attacks.
    *Application:* The template engine enforces *autoescaping* for all rendered variables by default. Any script injected by a malicious user will be rendered as safe text rather than executable code in the browser.
* **Flask-Login:** *Security Goal:* Secure session management.
    *Application:* Handles the user session lifecycle in a standardized way, protecting against session hijacking. It also manages the secure setting of session cookies (enforcing `HttpOnly` and `Secure` flags).
* **Flask-Limiter:** *Security Goal:* Protection against Brute-force and DoS (Denial of Service) attacks.
    *Application:* Allows applying rate limits to specific endpoints (e.g., the login form), effectively blocking IP addresses that attempt to guess passwords or overload the application with requests.
* **Flask-Migrate:** *Security Goal:* Data integrity and continuity.
    *Application:* Based on the Alembic library, it provides safe, version-controlled database schema migrations. It protects against data loss or corruption when modifying production data models.

## 3. Consequences

### Positive:
* **High OWASP Standard:** This architecture immediately mitigates the most critical vulnerabilities from the OWASP Top 10 list (Injection, Broken Authentication, XSS).
* **Efficiency (Solo Developer):** Leveraging proven libraries frees up my time, allowing for rapid delivery of new features without requiring me to be an expert in cryptography and network security.
* **Clean Code:** Extensions like `Flask-Login` and `Flask-Limiter` introduce elegant decorators (e.g., `@login_required`), keeping the core application code clean and readable.

### Negative / Constraints:
* **Vendor Lock-in:** The application is tightly coupled with the Flask ecosystem. A potential migration to another framework (e.g., FastAPI or Django) would require rewriting almost the entire authorization and data access layer.
* **Maintenance Overhead:** As a solo developer, I must regularly monitor and update all 7 libraries to ensure they do not contain newly discovered vulnerabilities (e.g., by utilizing tools like `safety` or `pip-audit`).
