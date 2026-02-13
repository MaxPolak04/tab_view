import click
from flask.cli import with_appcontext
from tab_view import db
from tab_view.models import User
from werkzeug.security import generate_password_hash
from .seed import seed_data  # Importujemy naszą nową funkcję


@click.command("seed-db")
@with_appcontext
def seed_db_command():
    """Populates the database with initial data (Tags, Default Media)."""
    seed_data()
    click.echo(click.style("Database seeded successfully!", fg="green"))


@click.command("create-user")
@click.argument("username")
@click.argument("password")
@click.option("--admin", is_flag=True, help="Set user as admin")
@with_appcontext
def create_user_command(username, password, admin):
    """Creates a new user via CLI."""
    if User.query.filter_by(username=username).first():
        click.echo(click.style(f'Error: User "{username}" already exists!', fg="red"))
        return

    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password, is_admin=admin)

    db.session.add(user)
    db.session.commit()

    role = "Admin" if admin else "User"
    click.echo(click.style(f"Success! Created {role}: {username}", fg="green"))
