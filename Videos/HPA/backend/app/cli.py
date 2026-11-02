"""Flask CLI commands for administrative and operational tasks."""

import click
from flask.cli import with_appcontext
from app.db import execute_query
from app.auth import hash_password

@click.command("init-admin")
@click.option("--username", prompt="Administrator username", help="Username for the new administrator")
@click.option("--fullname", prompt="Full name", default="Hospital Administrator", help="Full name of administrator")
@click.option("--email", prompt="Email address", help="Email of administrator")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Secure password")
@with_appcontext
def init_admin_command(username, fullname, email, password):
    """Securely initialize or reset the first Administrator account."""
    username = username.strip()
    fullname = fullname.strip()
    email = email.strip()
    password = password.strip()

    if not username or len(username) < 3:
        click.echo(click.style("[ERROR] Username must be at least 3 characters.", fg="red"))
        return

    if not password or len(password) < 6:
        click.echo(click.style("[ERROR] Password must be at least 6 characters.", fg="red"))
        return

    existing = execute_query(
        "SELECT user_id, username, role FROM users WHERE username = %s",
        (username,),
        fetch="one"
    )

    pwd_hash = hash_password(password)

    if existing:
        click.echo(f"User '{username}' already exists (Role: {existing['role']}).")
        if click.confirm("Do you want to promote/reset this user as an active Administrator?", default=True):
            execute_query(
                """
                UPDATE users 
                SET password_hash = %s, full_name = %s, email = %s, role = 'administrator', is_active = 1
                WHERE user_id = %s
                """,
                (pwd_hash, fullname, email, existing["user_id"]),
                commit=True
            )
            click.echo(click.style(f"[SUCCESS] User '{username}' updated to active Administrator.", fg="green"))
    else:
        execute_query(
            """
            INSERT INTO users (username, password_hash, full_name, email, role, is_active)
            VALUES (%s, %s, %s, %s, 'administrator', 1)
            """,
            (username, pwd_hash, fullname, email),
            commit=True
        )
        click.echo(click.style(f"[SUCCESS] Administrator '{username}' created successfully!", fg="green"))
        click.echo(f"Role: administrator | Email: {email} | Status: Active")

def register_commands(app):
    """Register custom CLI commands with the Flask application."""
    app.cli.add_command(init_admin_command)
