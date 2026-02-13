import pytest
from sqlalchemy.exc import IntegrityError
from tab_view.models import User


def test_create_user(init_database):
    """
    Verifies that a user can be successfully created with valid data.
    """
    user = User(username="testuser", password="hashedpassword", is_admin=False)

    init_database.session.add(user)
    init_database.session.commit()

    assert user.id is not None
    assert user.username == "testuser"


def test_user_repr(init_database):
    """
    Tests the string representation (__repr__) of the User model.
    """
    user = User(username="john", password="secret")
    init_database.session.add(user)
    init_database.session.commit()

    assert repr(user) == "<User john>"


def test_user_requires_username(init_database):
    """
    Verifies that creating a user without a username raises an IntegrityError
    (testing nullable=False constraint).
    """
    user = User(password="secret")
    init_database.session.add(user)

    with pytest.raises(IntegrityError):
        init_database.session.commit()

    init_database.session.rollback()


def test_username_must_be_unique(init_database):
    """
    Verifies that usernames must be unique across the database.
    Attempting to create a duplicate username should raise an IntegrityError.
    """
    user1 = User(username="admin", password="123")
    user2 = User(username="admin", password="456")

    init_database.session.add(user1)
    init_database.session.commit()

    init_database.session.add(user2)
    with pytest.raises(IntegrityError):
        init_database.session.commit()

    init_database.session.rollback()


def test_user_is_not_admin_by_default(init_database):
    """
    Verifies that the is_admin flag defaults to False when not specified.
    """
    user = User(username="normal", password="123")
    init_database.session.add(user)
    init_database.session.commit()

    assert user.is_admin is False


def test_user_created_at_is_set(init_database):
    """
    Verifies that the created_at timestamp is automatically set by the database
    upon insertion (server_default).
    """
    user = User(username="time", password="123")
    init_database.session.add(user)
    init_database.session.commit()

    init_database.session.refresh(user)

    assert user.created_at is not None
