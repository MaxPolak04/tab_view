import pytest
from sqlalchemy.exc import IntegrityError
from tab_view.models import User


def test_create_user(database):
    user = User(
        username='testuser',
        password='hashedpassword',
        is_admin=False
    )

    database.session.add(user)
    database.session.commit()

    assert user.id is not None
    assert user.username == 'testuser'


def test_user_repr(database):
    user = User(username='john', password='secret')
    database.session.add(user)
    database.session.commit()

    assert repr(user) == '<User john>'


def test_user_requires_username(database):
    user = User(password="secret")
    database.session.add(user)

    with pytest.raises(IntegrityError):
        database.session.commit()


def test_username_must_be_unique(database):
    user1 = User(username="admin", password="123")
    user2 = User(username="admin", password="456")

    database.session.add(user1)
    database.session.commit()

    database.session.add(user2)
    with pytest.raises(IntegrityError):
        database.session.commit()


def test_user_is_not_admin_by_default(database):
    user = User(username="normal", password="123")
    database.session.add(user)
    database.session.commit()

    assert user.is_admin is False


def test_user_created_at_is_set(database):
    user = User(username="time", password="123")
    database.session.add(user)
    database.session.commit()

    assert user.created_at is not None

