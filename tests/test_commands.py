from tab_view.models import User
from unittest.mock import patch


def test_seed_db_command(runner, init_database):
    """
    Test the CLI command 'seed-db'.
    It should execute successfully and populate the database.
    """
    # We must patch 'seed_data' inside 'tab_view.commands' because that is where
    # it is imported and used. Patching 'tab_view.seed.seed_data' would not work
    # if commands.py has already imported the function.
    with patch("tab_view.commands.seed_data") as mock_seed:
        result = runner.invoke(args=["seed-db"])

        assert result.exit_code == 0
        assert "Database seeded successfully!" in result.output
        assert mock_seed.called


def test_create_user_command_success(runner, init_database):
    """
    Test creating a regular user via CLI.
    Command: flask create-user <username> <password>
    """
    result = runner.invoke(args=["create-user", "cli_user", "password123"])

    assert result.exit_code == 0
    assert "Success! Created User: cli_user" in result.output

    # Verify in Database
    user = User.query.filter_by(username="cli_user").first()
    assert user is not None
    assert user.is_admin is False


def test_create_admin_command_success(runner, init_database):
    """
    Test creating an admin user via CLI using the --admin flag.
    """
    result = runner.invoke(args=["create-user", "admin_user", "secret", "--admin"])

    assert result.exit_code == 0
    assert "Success! Created Admin: admin_user" in result.output

    user = User.query.filter_by(username="admin_user").first()
    assert user is not None
    assert user.is_admin is True


def test_create_user_duplicate_fails(runner, init_database):
    """
    Test that the CLI command handles duplicate usernames gracefully.
    """
    # Create first user
    runner.invoke(args=["create-user", "duplicate_user", "pass1"])

    # Attempt to create the same user again
    result = runner.invoke(args=["create-user", "duplicate_user", "pass2"])

    # The command returns exit code 0 but prints an error message
    assert result.exit_code == 0
    assert 'Error: User "duplicate_user" already exists!' in result.output

    # Ensure only one user exists
    assert User.query.filter_by(username="duplicate_user").count() == 1
