# Quality Assurance

TabView maintains a strict testing regime to ensure code stability and prevent regressions.

## Test Suite Overview

All tests are located in the `/tests` directory and utilize the `pytest` framework. The suite is designed to be highly verifiable and isolated, leveraging fixtures defined in `conftest.py`.

## Test Categories

- **Unit Tests:** Located in `test_models/` and `test_utils/`. These test the absolute core logic, such as data models (`test_device.py`, `test_event.py`) and utility functions (`test_detect_type.py`, `test_str_to_bool.py`).
- **Integration Tests:** Located in `test_views/`. These tests validate full request-response cycles, API endpoints, and authentication flows (Auth, Devices, Media, Events).

## Test Execution

To execute the entire test suite locally:

```bash
uv run pytest
```

## Code Coverage

To generate a coverage report and ensure newly developed features meet testing requirements:

```bash
pytest --cov
```
