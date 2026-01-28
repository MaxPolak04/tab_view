from flask import url_for
from werkzeug.security import check_password_hash
from tab_view.models import User

# --- PERMISSIONS TESTS ---

def test_users_page_forbidden_for_non_admin(auth_client):
    """
    Verify that a regular user cannot access the user management list.
    """
    response = auth_client.get(url_for('users.get_all_users'))
    assert response.status_code == 403


def test_create_user_forbidden_for_non_admin(auth_client):
    """
    Verify that a regular user cannot create new users.
    """
    response = auth_client.get(url_for('users.create_user'))
    assert response.status_code == 403


# --- CREATE USER TESTS ---

def test_create_user_success(admin_client, init_database):
    """
    Test successful creation of a new user by an admin.
    """
    # 1. Submit form
    # UWAGA: Aby checkbox 'is_admin' był False, NIE WYSYŁAMY go w ogóle w data.
    # Wysłanie 'is_admin': False zamienia się na string "False", co WTForms uznaje za True!
    response = admin_client.post(url_for('users.create_user'), data={
        'username': 'new_emp',
        'password': 'SecretPassword123!',
        'confirm_password': 'SecretPassword123!'
        # 'is_admin': False  <--- USUNIĘTO (to oznacza False)
    }, follow_redirects=True)

    # 2. Assert
    assert response.status_code == 200
    assert b"User created successfully" in response.data

    # 3. Verify Database
    new_user = User.query.filter_by(username='new_emp').first()
    assert new_user is not None
    assert check_password_hash(new_user.password, 'SecretPassword123!')
    assert new_user.is_admin is False  # Teraz to przejdzie


def test_create_duplicate_user_fails(admin_client, init_database):
    """
    Test that creating a user with an existing username shows an error.
    """
    # 1. Create user manually
    user = User(username='existing_user', password='x')
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Try to create same user via form
    response = admin_client.post(url_for('users.create_user'), data={
        'username': 'existing_user',
        'password': 'SecretPassword123!',         # Używamy silnego hasła dla pewności
        'confirm_password': 'SecretPassword123!'  # Ważne: potwierdzenie hasła
        # 'is_admin': ... (brak klucza = False)
    }, follow_redirects=True)

    # 3. Assert
    # Sprawdzamy, czy formularz wrócił z błędem o duplikacie
    assert b"Username already exists" in response.data
    
    # Upewniamy się, że w bazie nadal jest tylko 1 taki użytkownik
    assert User.query.filter_by(username='existing_user').count() == 1


def test_update_user_change_password(admin_client, init_database):
    """
    Test updating a user's password.
    Verifies that the password hash in the database actually changes.
    """
    # 1. Setup victim user
    user = User(username='staff', password='OldPassword')
    init_database.session.add(user)
    init_database.session.commit()
    
    old_password_hash = user.password

    # 2. Update via form
    response = admin_client.post(url_for('users.update_user', user_id=user.id), data={
        'username': 'staff',
        'password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
        # 'is_admin': ... (brak klucza = False)
    }, follow_redirects=True)

    # 3. Assert
    assert b"User updated successfully" in response.data
    
    # Refresh object from DB
    init_database.session.refresh(user)
    
    assert user.password != old_password_hash
    assert check_password_hash(user.password, 'NewPassword123!')


# --- DELETE USER TESTS ---

def test_delete_other_user_success(admin_client, init_database):
    """
    Test that admin can delete another user.
    """
    # 1. Setup
    user = User(username='fired_emp', password='x')
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Act
    response = admin_client.post(
        url_for('users.delete_user', user_id=user.id),
        follow_redirects=True
    )

    # 3. Assert
    assert b"User deleted successfully" in response.data
    assert User.query.get(user.id) is None


def test_delete_self_blocked(admin_client, init_database):
    """
    CRITICAL TEST: Verify that admin cannot delete their own account.
    """
    # 1. Find the current admin user (created by admin_client fixture)
    admin_user = User.query.filter_by(username='admin').first()
    assert admin_user is not None

    # 2. Attempt to delete self
    response = admin_client.post(
        url_for('users.delete_user', user_id=admin_user.id),
        follow_redirects=True
    )

    # 3. Assert
    assert b"You cannot delete your own account" in response.data
    
    # Verify admin still exists in DB
    reloaded_admin = User.query.get(admin_user.id)
    assert reloaded_admin is not None
