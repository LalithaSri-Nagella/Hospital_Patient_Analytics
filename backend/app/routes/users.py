"""User Management Routes Blueprint for Hospital Administrators."""

import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from app.db import execute_query
from app.auth import roles_required, hash_password, get_current_user

users_bp = Blueprint("users", __name__)

ALLOWED_ROLES = ["doctor", "accountant", "administrator"]
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@users_bp.route("/users", endpoint="users_list")
@roles_required("administrator")
def users_list():
    """Display list of authorized hospital users with filtering and status indicators."""
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role", "").strip()
    status_filter = request.args.get("status", "").strip()

    conditions = []
    params = []

    if search:
        conditions.append("(username LIKE %s OR full_name LIKE %s OR email LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if role_filter and role_filter in ALLOWED_ROLES:
        conditions.append("role = %s")
        params.append(role_filter)

    if status_filter in ("active", "inactive"):
        conditions.append("is_active = %s")
        params.append(1 if status_filter == "active" else 0)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT user_id, username, full_name, email, role, is_active, created_at, updated_at
        FROM users
        {where_clause}
        ORDER BY created_at DESC
    """
    users = execute_query(sql, tuple(params), fetch="all")

    # Count statistics for header summary badges
    total_users = len(users)
    active_count = sum(1 for u in users if u["is_active"])

    return render_template(
        "user_management.html",
        users=users,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter,
        total_users=total_users,
        active_count=active_count,
        allowed_roles=ALLOWED_ROLES
    )

@users_bp.route("/users/new", methods=["GET", "POST"], endpoint="user_create")
@roles_required("administrator")
def user_create():
    """Create a new authorized hospital staff account (Administrator, Doctor, or Accountant)."""
    errors = {}
    form_data = {
        "username": "",
        "full_name": "",
        "email": "",
        "role": "doctor"
    }

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        form_data = {
            "username": username,
            "full_name": full_name,
            "email": email,
            "role": role
        }

        if not username or len(username) < 3 or len(username) > 50:
            errors["username"] = "Username must be between 3 and 50 characters."
        elif not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            errors["username"] = "Username may only contain letters, numbers, dots, and underscores."
        else:
            existing_user = execute_query(
                "SELECT user_id FROM users WHERE username = %s",
                (username,),
                fetch="one"
            )
            if existing_user:
                errors["username"] = f"Username '{username}' is already in use."

        if not full_name or len(full_name) < 2:
            errors["full_name"] = "Full name is required (at least 2 characters)."

        if not email or not EMAIL_REGEX.match(email):
            errors["email"] = "A valid email address is required."

        if role not in ALLOWED_ROLES:
            errors["role"] = f"Role must be one of: {', '.join(ALLOWED_ROLES)}."

        if not password or len(password) < 6:
            errors["password"] = "Password must be at least 6 characters long."
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            pwd_hash = hash_password(password)
            execute_query(
                """
                INSERT INTO users (username, password_hash, full_name, email, role, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
                """,
                (username, pwd_hash, full_name, email, role),
                commit=True
            )
            flash(f"User account '{username}' ({role.title()}) created successfully!", "success")
            return redirect(url_for("users.users_list"))

    return render_template(
        "user_form.html",
        action="Create",
        form_data=form_data,
        errors=errors,
        allowed_roles=ALLOWED_ROLES
    )

@users_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"], endpoint="user_edit")
@roles_required("administrator")
def user_edit(user_id):
    """Edit account metadata and role for an existing user."""
    user = execute_query(
        "SELECT user_id, username, full_name, email, role, is_active FROM users WHERE user_id = %s",
        (user_id,),
        fetch="one"
    )
    if not user:
        flash(f"User #{user_id} not found.", "danger")
        return redirect(url_for("users.users_list"))

    errors = {}
    form_data = {
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"]
    }

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "").strip()

        form_data["full_name"] = full_name
        form_data["email"] = email
        form_data["role"] = role

        if not full_name or len(full_name) < 2:
            errors["full_name"] = "Full name is required."

        if not email or not EMAIL_REGEX.match(email):
            errors["email"] = "A valid email address is required."

        if role not in ALLOWED_ROLES:
            errors["role"] = "Invalid role specified."

        # Guard: Check if demoting the last active administrator
        if user["role"] == "administrator" and role != "administrator":
            admin_count = execute_query(
                "SELECT COUNT(*) AS total FROM users WHERE role = 'administrator' AND is_active = 1",
                fetch="one"
            )["total"]
            if admin_count <= 1:
                errors["role"] = "Cannot change role: At least one active administrator is required to manage the system."

        if not errors:
            execute_query(
                "UPDATE users SET full_name = %s, email = %s, role = %s WHERE user_id = %s",
                (full_name, email, role, user_id),
                commit=True
            )
            flash(f"User account '{user['username']}' updated successfully!", "success")
            return redirect(url_for("users.users_list"))

    return render_template(
        "user_form.html",
        action="Edit",
        user_id=user_id,
        form_data=form_data,
        errors=errors,
        allowed_roles=ALLOWED_ROLES
    )

@users_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"], endpoint="user_toggle_status")
@roles_required("administrator")
def user_toggle_status(user_id):
    """Activate or deactivate a user account with safeguards for active admins."""
    current_u = get_current_user()

    # Safety guard 1: Prevent self-deactivation
    if current_u.id == user_id:
        flash("Action Blocked: You cannot deactivate your own currently active administrator account.", "danger")
        return redirect(url_for("users.users_list"))

    user = execute_query(
        "SELECT user_id, username, role, is_active FROM users WHERE user_id = %s",
        (user_id,),
        fetch="one"
    )
    if not user:
        flash(f"User #{user_id} not found.", "danger")
        return redirect(url_for("users.users_list"))

    new_status = 0 if user["is_active"] else 1

    # Safety guard 2: Prevent deactivating the last active administrator
    if user["role"] == "administrator" and new_status == 0:
        active_admins = execute_query(
            "SELECT COUNT(*) AS total FROM users WHERE role = 'administrator' AND is_active = 1",
            fetch="one"
        )["total"]
        if active_admins <= 1:
            flash("Action Blocked: Cannot deactivate the last active administrator in the system.", "danger")
            return redirect(url_for("users.users_list"))

    execute_query(
        "UPDATE users SET is_active = %s WHERE user_id = %s",
        (new_status, user_id),
        commit=True
    )

    action_text = "activated" if new_status == 1 else "deactivated"
    flash(f"User account '{user['username']}' has been {action_text} successfully.", "success")
    return redirect(url_for("users.users_list"))

@users_bp.route("/users/<int:user_id>/reset-password", methods=["POST"], endpoint="user_reset_password")
@roles_required("administrator")
def user_reset_password(user_id):
    """Securely reset an authorized user's password."""
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    user = execute_query("SELECT user_id, username FROM users WHERE user_id = %s", (user_id,), fetch="one")
    if not user:
        flash(f"User #{user_id} not found.", "danger")
        return redirect(url_for("users.users_list"))

    if not new_password or len(new_password) < 6:
        flash("Password reset failed: Password must be at least 6 characters long.", "danger")
        return redirect(url_for("users.users_list"))

    if new_password != confirm_password:
        flash("Password reset failed: Passwords do not match.", "danger")
        return redirect(url_for("users.users_list"))

    pwd_hash = hash_password(new_password)
    execute_query(
        "UPDATE users SET password_hash = %s WHERE user_id = %s",
        (pwd_hash, user_id),
        commit=True
    )
    flash(f"Password for user '{user['username']}' has been reset successfully.", "success")
    return redirect(url_for("users.users_list"))
