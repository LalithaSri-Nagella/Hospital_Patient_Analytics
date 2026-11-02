"""Authentication Routes Blueprint for Hospital Management Portal."""

from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.db import execute_query
from app.auth import login_user, logout_user, verify_password, get_current_user, get_role_dashboard_url

auth_bp = Blueprint("auth", __name__)

def is_safe_redirect_url(target):
    """Ensure redirect URL belongs to the current application host and prevents open-redirect vulnerabilities."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    """Handle secure hospital portal user login."""
    current_u = get_current_user()
    if current_u.is_authenticated:
        return redirect(get_role_dashboard_url(current_u.role))

    errors = {}
    form_data = {"username": "", "remember": False}
    next_page = request.args.get("next", "").strip()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        form_data["username"] = username
        form_data["remember"] = remember

        if not username:
            errors["username"] = "Please enter your username."
        if not password:
            errors["password"] = "Please enter your password."

        if not errors:
            user = execute_query(
                """
                SELECT user_id, username, password_hash, full_name, email, role, is_active
                FROM users
                WHERE username = %s
                """,
                (username,),
                fetch="one"
            )

            if not user or not verify_password(password, user["password_hash"]):
                flash("Invalid username or password. Please verify your credentials and try again.", "danger")
            elif not user["is_active"]:
                flash("Your account is currently inactive. Please contact the hospital administrator.", "danger")
            else:
                login_user(user, remember=remember)
                flash(f"Welcome back, {user['full_name']} ({user['role'].title()})!", "success")

                if next_page and is_safe_redirect_url(next_page) and next_page != "/login":
                    return redirect(next_page)
                return redirect(get_role_dashboard_url(user["role"]))

    return render_template(
        "login.html",
        form_data=form_data,
        errors=errors,
        next_page=next_page
    )

@auth_bp.route("/logout", methods=["GET", "POST"], endpoint="logout")
def logout():
    """Handle user logout, destroying session and authentication tokens."""
    logout_user()
    flash("You have been successfully logged out of the portal.", "info")
    return redirect(url_for("auth.login"))
