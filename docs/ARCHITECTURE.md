# Architecture & Deep Tech Dive

This document outlines the core engineering decisions and technical mechanisms that power TabView.

## Real-Time Display Engine
The frontend client operating on the tablets is completely autonomous. Instead of relying on WebSocket connections which can be unstable on mobile networks, it utilizes a robust polling mechanism. The JavaScript engine calls `setInterval(fetchState, 60 * 1000)` to query the API every 60 seconds, seamlessly updating media queues and hardware statuses without ever reloading the page.

## Smart Fallback System
To ensure a tablet never displays a "black screen" when an event schedule expires or is empty, TabView implements a Smart Fallback System. The logic automatically serves "Default Media" (e.g., `default.jpg` or a corporate logo) whenever the queue is empty, guaranteeing uninterrupted visual communication.

## Live Weather & Caching Strategy
The weather widget relies on the public Open-Meteo API. To prevent rate-limiting and minimize unnecessary network overhead from multiple tablets constantly polling the backend:
* An **In-Memory Cache** (`WeatherService`) is implemented.
* The cache has a strict Time-To-Live (TTL) of **20 minutes** (`WEATHER_CACHE_MINUTES = 20`).
* Coordinates are strictly decoupled and customizable via `.env`.

## Responsive UI Scaling (4K Support)
Traditional CSS frameworks like Bootstrap (and its RFS utility) often hit a hard ceiling at 1200px width. TabView required pixel-perfect rendering across hardware ranging from 800p tablets to 4K displays.
To achieve this, we abandoned standard font classes (like `fs-2` or `display-4`) in critical display views (`display.js`, `clock.html`). Instead, we implemented a custom scaling architecture using viewport units (`vh` and `vw`). Elements are built using glassmorphism aesthetics (e.g., `backdrop-filter: blur(12px)`) and asymmetrical borders (`border-radius: 4vh 0 0 4vh`) that scale fluidly regardless of physical screen density.

## Security Architecture & Background Processing

### Enterprise Audit Logging
Every administrative action (CRUD operations) is recorded using the `AuditLog` model. The system captures the timestamp, exact action, affected entity, user ID, **IP address**, and **UserAgent**, providing an enterprise-grade forensic trail.

### Overlap Prevention
The backend enforces data integrity by rejecting overlapping calendar events. When scheduling via the API or FullCalendar UI, the application dynamically verifies the `start` and `end` parameters to prevent temporal collisions on the same device.

### Shift-Left Integration
Security is integrated at the pipeline level using `Bandit` (SAST) and `Ruff` (linting). Secure filename handling (`secure_filename`) is strictly enforced on all uploads.

### Background Tasks
Heavy processing is offloaded from the main WSGI server. The `tasks.py` module handles asynchronous jobs via APScheduler, ensuring the main Gunicorn thread remains unblocked for API requests.
