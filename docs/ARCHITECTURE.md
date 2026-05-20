# Architecture & Deep Tech Dive

This document outlines the core engineering decisions, network topographies, and technical mechanisms that power TabView.

---

## 1. Real-Time Display Engine

The frontend client operating on the tablets is completely autonomous. Instead of relying on WebSocket connections which can be unstable or resource-heavy on low-power display tablets, it utilizes a robust, deterministic polling mechanism.

The JavaScript engine calls `setInterval(fetchState, 60 * 1000)` to query the backend API every 60 seconds. This approach seamlessly updates media queues and hardware statuses without ever triggering a full window or page reload, preserving visual continuity.

---

## 2. Smart Fallback System

To ensure a tablet never displays a disruptive "black screen" or a blank browser container when an event schedule expires or the queue is unpopulated, TabView implements a Smart Fallback System.

The backend application logic automatically serves a predefined "Default Media" asset sequence (e.g., `default.png` or corporate branding layouts from the `branding/` folder) whenever the active schedule queue is empty, guaranteeing uninterrupted visual communication.

---

## 3. Live Weather & Caching Strategy

The live weather widget integrated into the display interface relies on the public, external Open-Meteo API. To prevent API rate-limiting thresholds and minimize unnecessary network overhead from dozens of concurrent tablets constantly polling the application server, a caching strategy was engineered:

- **In-Memory Cache Layer (`WeatherService`):** Weather metrics are held in-memory to prevent downstream network calls.
- **Strict Time-To-Live (TTL):** The cache forces a refresh only after **20 minutes** have elapsed (`WEATHER_CACHE_MINUTES = 20`).
- **Decoupled Geolocation:** Coordinates are strictly parameterized and customizable via host environment variables (`WEATHER_LATITUDE` / `WEATHER_LONGITUDE`), defaulting to Poznań, Poland.

---

## 4. Responsive UI Scaling (4K Support)

Traditional CSS frameworks like Bootstrap (and its responsive fluid typography engine RFS) often hit a hard layout ceiling at 1200px widths. TabView required pixel-perfect, crisp rendering scaling fluidly across hardware variants ranging from low-end 800p devices up to dedicated 4K conference displays.

To bypass default framework limitations, we abandoned standard responsive font utilities (such as `fs-2` or `display-4`) in critical display views (`display.js`, `clock.html`). Instead, we implemented a custom layout scaling architecture driven entirely by relative viewport units (`vh` and `vw`). UI elements utilize fluid glassmorphism aesthetics (`backdrop-filter: blur(12px)`) and asymmetrical scaling borders (`border-radius: 4vh 0 0 4vh`) that render identically regardless of physical screen pixel densities.

---

## 5. RESTful API Architecture & Routing Matrix

The decoupled communications between autonomous display engines, interactive FullCalendar frontends, and the core Flask backend are managed via a structured `Flask-RESTful` API layer. The API is entirely stateless, exchanges payloads using standard `application/json`, and implements proper HTTP status code boundaries.

### Core Endpoints Matrix

| Blueprint / Route             | HTTP Method | Auth Required | Description / Payload Format                                                                                               |
| ----------------------------- | ----------- | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `/api/v1/events`              | `GET`       | Yes           | Retrieves full event schedules filtered by date ranges (`?start=...&end=...`) to feed FullCalendar instances.              |
| `/api/v1/events`              | `POST`      | Yes           | Provisions a new calendar event or recurring group series. Rejects overlapping timelines.                                  |
| `/api/v1/events/<int:id>`     | `PUT`       | Yes           | Modifies an existing scheduling record. Triggers real-time collision validation constraints.                               |
| `/api/v1/events/<int:id>`     | `DELETE`    | Yes           | Removes an event instance or group (`?scope=instance` / `?scope=group`). Logs administrative audit trails.                 |
| `/api/v1/events/availability` | `GET`       | Yes           | Live query endpoint utilized to verify device availability over a prospective timestamp window before committing a record. |

---

## 6. Security Architecture & Background Processing

### Enterprise Audit Logging

Every administrative intervention and destructive CRUD mutation is recorded within the application database using the specialized `AuditLog` database model. The recording wrapper captures the exact timestamp, action context (e.g., `CREATE`, `DELETE`), modified database entities, user references, the originating client's **IP Address**, and the browser's full **UserAgent** string to generate a tamper-evident forensic audit trail.

### Overlap Prevention Engine

The backend enforces complete temporal calendar data integrity by rejecting overlapping device schedules. When an administrative action attempts to commit or resize an event via the API or FullCalendar UI layout, the backend intercepts the parameters and runs atomic boundary validation queries:

```sql
SELECT * FROM events
WHERE device_id = :device_id
  AND start_time < :requested_end_time
  AND end_time > :requested_start_time;
```

If the verification wrapper discovers any temporal collision, the database operation is blocked, and an explicit `400 Bad Request` payload is returned to the user.

### Asynchronous Background Processing

Heavy, non-blocking operational maintenance tasks are cleanly offloaded from the main WSGI (`Gunicorn`) thread pool using `Flask-APScheduler`. This architecture isolates background operations to ensure zero UI sluggishness or endpoint timeout latency.

A primary example of this is the automated system maintenance job declared in `tasks.py`:

- **Audit Trail Rotations:** The `cleanup_old_audit_logs` worker awakens daily at exactly 03:00 AM via a cron trigger.
- **Database Optimization:** It executes a targeted deletion pass removing historical `AuditLog` records older than 90 days (`cutoff_date = datetime.now() - timedelta(days=90)`), keeping database storage footprints lean and indexing operations performant.

---

## 7. Architecture Decision Records (ADR)

The historical context and detailed engineering trade-offs behind our architectural evolution are captured inside standardized ADR immutable logs. Refer to the specific logs for internal design review:

- **[ADR 0001: Shift-Left Security and CI/CD](adr/0001-shift-left-security-and-ci-cd.md)** – Implementation strategy for mandatory automated security analysis within core repository push workflows.
- **[ADR 0002: Adoption of UV Package Manager](adr/0002-adoption-of-uv-package-manager.md)** – Architectural shift from traditional requirements paradigms to strict deterministic lockfiles driven by the `uv` ecosystem.
- **[ADR 0003: Implement Pre-commit](adr/0003-implement-pre-commit.md)** – Moving syntax validation boundaries directly into local developer pre-commit hook runtimes.
- **[ADR 0004: Security Architecture and Libraries](adr/0004-security-architecture-and-libraries.md)** – Criteria and rationale behind core library auditing, middleware choice, and secure encryption policies.
