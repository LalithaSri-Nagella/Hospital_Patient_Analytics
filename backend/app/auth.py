"""Authentication and Role-Based Authorization Utilities for Hospital Management System."""

from functools import wraps
from flask import session, redirect, url_for, request, flash, g, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import execute_query

class CurrentUser:
    """Convenience wrapper for the currently authenticated user in templates and requests."""
    def __init__(self, data=None):
        if data:
            self.is_authenticated = True
            self.id = data.get("user_id")
            self.username = data.get("username", "")
            self.full_name = data.get("full_name", "")
            self.email = data.get("email", "")
            self.role = data.get("role", "")
            self.is_active = bool(data.get("is_active", True))
        else:
            self.is_authenticated = False
            self.id = None
            self.username = ""
            self.full_name = "Guest"
            self.email = ""
            self.role = ""
            self.is_active = False

    def is_admin(self):
        return self.role == "administrator"

    def is_doctor(self):
        return self.role == "doctor"

    def is_accountant(self):
        return self.role == "accountant"

    def has_role(self, *roles):
        return self.is_authenticated and self.role in roles

    def __repr__(self):
        return f"<CurrentUser id={self.id} username='{self.username}' role='{self.role}'>"


def get_current_user():
    """Retrieve the current user from session and verify active status against database."""
    if "current_user" in g:
        return g.current_user

    user_id = session.get("user_id")
    if not user_id:
        g.current_user = CurrentUser(None)
        return g.current_user

    # Fetch live record from DB to guarantee up-to-date role and activation status
    try:
        user_row = execute_query(
            "SELECT user_id, username, full_name, email, role, is_active FROM users WHERE user_id = %s",
            (user_id,),
            fetch="one"
        )
        if user_row and user_row.get("is_active"):
            g.current_user = CurrentUser(user_row)
        else:
            # User was deleted or deactivated
            session.clear()
            g.current_user = CurrentUser(None)
    except Exception:
        # Fallback if DB check temporarily fails
        g.current_user = CurrentUser({
            "user_id": session.get("user_id"),
            "username": session.get("username", ""),
            "full_name": session.get("full_name", ""),
            "email": session.get("email", ""),
            "role": session.get("user_role", ""),
            "is_active": True
        })

    return g.current_user


def login_user(user_dict, remember=False):
    """Store authenticated user identity in session with optional persistent cookie."""
    session.clear()
    session["user_id"] = user_dict["user_id"]
    session["username"] = user_dict["username"]
    session["full_name"] = user_dict["full_name"]
    session["email"] = user_dict["email"]
    session["user_role"] = user_dict["role"]
    session.permanent = bool(remember)
    g.current_user = CurrentUser(user_dict)


def logout_user():
    """Clear the session completely upon logout."""
    session.clear()
    g.current_user = CurrentUser(None)


def get_role_dashboard_url(role):
    """Determine the default landing dashboard URL based on assigned user role."""
    if role == "doctor":
        return url_for("analytics.doctor_dashboard")
    elif role == "accountant":
        return url_for("analytics.accountant_dashboard")
    else:
        return url_for("analytics.dashboard")


def login_required(view_func):
    """Decorator requiring the user to be authenticated and active."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        current_u = get_current_user()
        if not current_u.is_authenticated:
            next_url = request.full_path if request.method == "GET" and request.path != "/login" else None
            flash("Please log in to access this portal page.", "warning")
            return redirect(url_for("auth.login", next=next_url))

        return view_func(*args, **kwargs)
    return decorated_view


def roles_required(*allowed_roles):
    """Decorator requiring the user to have one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(*args, **kwargs):
            current_u = get_current_user()
            if not current_u.is_authenticated:
                next_url = request.full_path if request.method == "GET" and request.path != "/login" else None
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login", next=next_url))

            if current_u.role not in allowed_roles:
                if request.method == "POST":
                    abort(403, description=f"Access Denied: Your role '{current_u.role}' is not authorized to perform this action.")
                
                flash(f"Access Denied: Your role ('{current_u.role.title()}') does not have permission to access that section.", "danger")
                return redirect(get_role_dashboard_url(current_u.role))

            return view_func(*args, **kwargs)
        return decorated_view
    return decorator


def hash_password(password: str) -> str:
    """Hash a password using Werkzeug's secure hashing algorithm."""
    return generate_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain password against a stored Werkzeug hash."""
    return check_password_hash(hashed_password, plain_password)
