from unittest.mock import patch

from flask import url_for
from werkzeug.security import generate_password_hash

from tab_view.models import User

# --- GET / ACCESS TESTS ---


def test_signin_page_loads(client):
    """
    Test if the sign-in page loads correctly with status code 200.
    """
    response = client.get(url_for("auth.signin"))
    assert response.status_code == 200
    assert b"Sign In" in response.data


def test_signout_unauthorized(client):
    """
    Test that accessing signout without logging in redirects to login or unauthorized.
    """
    response = client.get(url_for("auth.signout"), follow_redirects=False)
    assert response.status_code in [302, 401]


# --- POST / LOGIC TESTS ---


def test_signin_successful_without_remember_me(client, init_database):
    """
    Test successful login with correct credentials and remember_me=False.
    Verifies redirection and flash message.
    """
    # 1. Setup: Create a user with a HASHED password
    hashed_password = generate_password_hash("correct_password")
    user = User(username="test_admin", password=hashed_password)
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Act: Post valid credentials without 'remember_me'
    response = client.post(
        url_for("auth.signin"),
        data={"username": "test_admin", "password": "correct_password"},
        follow_redirects=True,
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"Logged in successfully!" in response.data


def test_signin_successful_with_remember_me(client, init_database):
    """
    Test successful login with correct credentials and remember_me=True.
    """
    hashed_password = generate_password_hash("correct_password")
    user = User(username="test_remember", password=hashed_password)
    init_database.session.add(user)
    init_database.session.commit()

    # Form sends 'y' or 'True' when checkbox is checked
    response = client.post(
        url_for("auth.signin"),
        data={
            "username": "test_remember",
            "password": "correct_password",
            "remember_me": "y",
        },
        follow_redirects=True,
    )

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


def test_signin_db_error_on_last_login(client, init_database):
    """
    Test that login succeeds even if the database fails to update 'last_login_at'.
    Verifies that the except block handles the rollback gracefully.
    """
    hashed_password = generate_password_hash("correct_password")
    user = User(username="test_db_error", password=hashed_password)
    init_database.session.add(user)
    init_database.session.commit()

    # Symulujemy błąd bazy danych w momencie zapisu daty ostatniego logowania
    with patch("tab_view.auth.routes.db.session.commit") as mock_commit:
        mock_commit.side_effect = Exception("Mocked database lock")

        response = client.post(
            url_for("auth.signin"),
            data={"username": "test_db_error", "password": "correct_password"},
            follow_redirects=True,
        )

    # Logowanie powinno się udać, aplikacja nie może wybuchnąć mimo błędu DB
    assert response.status_code == 200
    assert b"Logged in successfully!" in response.data


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
    assert response.status_code == 200
