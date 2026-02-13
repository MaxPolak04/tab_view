import pytest

from tab_view import create_app
from tab_view.config import TestingConfig


def test_404_html_render(client):
    """
    Test standard 404 error for browser users.
    Should return HTML template.
    We explicitly ask for text/html to avoid ambiguity in content negotiation.
    """
    # 1. Request non-existent page with explicit HTML accept header
    response = client.get(
        "/this-url-definitely-does-not-exist", headers={"Accept": "text/html"}
    )

    # 2. Assert
    assert response.status_code == 404
    assert "text/html" in response.content_type
    assert b"Not Found" in response.data


def test_404_api_json_response(client):
    """
    Test 404 error for API requests.
    Should return JSON based on URL prefix (/api/).
    """
    # 1. Request non-existent API endpoint
    response = client.get("/api/v1/ghost-endpoint")

    # 2. Assert
    assert response.status_code == 404
    assert response.is_json

    data = response.get_json()
    assert data["code"] == 404
    assert data["error"] == "Not Found"


def test_404_json_via_accept_header(client):
    """
    Test 404 error when client explicitly asks for JSON via headers
    (even if not in /api/ path).
    """
    # 1. Request standard URL but ask for JSON
    response = client.get("/some-page", headers={"Accept": "application/json"})

    # 2. Assert
    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["error"] == "Not Found"


# --- 500 Error Tests ---
# We cannot use the shared 'app' fixture here because we need to register
# new routes (@app.route), which is forbidden after
#  the app has started handling requests.
# Instead, we create a fresh app instance locally for these specific tests.


@pytest.fixture
def fresh_app():
    """Create a fresh app instance for 500 tests."""
    app = create_app(TestingConfig)
    return app


def test_500_html_render(fresh_app):
    """
    Test 500 error handling for standard views.
    """

    # 1. Register a broken route on the FRESH app
    @fresh_app.route("/force-crash")
    def crash():
        raise Exception("This is a simulated crash!")

    # 2. Create a client from this fresh app
    client = fresh_app.test_client()

    # 3. Act
    response = client.get("/force-crash", headers={"Accept": "text/html"})

    # 4. Assert
    assert response.status_code == 500
    assert "text/html" in response.content_type
    assert b"Internal Server Error" in response.data


def test_500_api_json_response(fresh_app):
    """
    Test 500 error handling for API.
    """

    # 1. Register broken API route
    @fresh_app.route("/api/force-crash")
    def api_crash():
        raise Exception("API failure")

    client = fresh_app.test_client()

    # 2. Act
    response = client.get("/api/force-crash")

    # 3. Assert
    assert response.status_code == 500
    assert response.is_json

    data = response.get_json()
    assert data["code"] == 500
    assert data["error"] == "Internal Server Error"
