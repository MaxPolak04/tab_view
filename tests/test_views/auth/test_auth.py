from flask import url_for
from werkzeug.security import generate_password_hash

from tab_view.models import User


def test_signin_page_loads(client):
    """
    Test if the sign-in page loads correctly with status code 200.
    """
    response = client.get(url_for("auth.signin"))
    assert response.status_code == 200
    assert b"Sign In" in response.data


def test_signin_successful(client, init_database):
    """
    Test successful login with correct credentials.
    Verifies redirection and flash message.
    """
    # 1. Setup: Create a user with a HASHED password
    hashed_password = generate_password_hash("correct_password")
    user = User(username="test_admin", password=hashed_password)
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Act: Post valid credentials
    # follow_redirects=True allows us to see the result page and flash messages
    response = client.post(
        url_for("auth.signin"),
        data={"username": "test_admin", "password": "correct_password"},
        follow_redirects=True,
    )

    # 3. Assert
    # Check if we landed on the devices page (based on your controller logic)
    # Note: Checking the path requires request context or checking page content
    assert response.status_code == 200
    assert b"Logged in successfully!" in response.data


def test_signin_wrong_password(client, init_database):
    """
    Test login attempt with incorrect password.
    Should redirect back to signin and show error message.
    """
    # 1. Setup
    hashed_password = generate_password_hash("correct_password")
    user = User(username="test_user", password=hashed_password)
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Act: Post WRONG password
    response = client.post(
        url_for("auth.signin"),
        data={"username": "test_user", "password": "wrong_password"},
        follow_redirects=True,
    )

    # 3. Assert
    assert b"Incorrect password!" in response.data
    # Should still show the Sign In form
    assert b"Sign In" in response.data


def test_signin_user_not_found(client, init_database):
    """
    Test login attempt with non-existent username.
    """
    response = client.post(
        url_for("auth.signin"),
        data={"username": "ghost_user", "password": "any_password"},
        follow_redirects=True,
    )

    assert b"User not found!" in response.data


def test_signout(client, init_database):
    """
    Test the signout functionality.
    Requires logging in first.
    """
    # 1. Setup: Create user
    hashed_password = generate_password_hash("secret")
    user = User(username="logout_tester", password=hashed_password)
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Login
    client.post(
        url_for("auth.signin"),
        data={"username": "logout_tester", "password": "secret"},
        follow_redirects=True,
    )

    # 3. Act: Logout
    response = client.get(url_for("auth.signout"), follow_redirects=True)

    # 4. Assert
    assert b"Logged out successfully!" in response.data
    # Usually redirects to index
    assert response.status_code == 200
