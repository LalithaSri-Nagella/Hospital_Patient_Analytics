"""Department Management Routes Blueprint."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import execute_query

departments_bp = Blueprint("departments", __name__)

@departments_bp.route("/departments", endpoint="departments_list")
def departments_list():
    departments = execute_query(
        """
        SELECT 
            d.department_id,
            d.department_name,
            COUNT(v.visit_id) AS total_visits
        FROM departments d
        LEFT JOIN visits v ON d.department_id = v.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY d.department_name ASC
        """,
        fetch="all"
    )
    return render_template("departments.html", departments=departments)

@departments_bp.route("/departments/new", methods=["GET", "POST"], endpoint="department_create")
def department_create():
    errors = {}
    department_name = ""
    
    if request.method == "POST":
        department_name = request.form.get("department_name", "").strip()
        
        if not department_name:
            errors["department_name"] = "Department name is required."
        elif len(department_name) < 2 or len(department_name) > 100:
            errors["department_name"] = "Department name must be between 2 and 100 characters."
        else:
            existing = execute_query(
                "SELECT department_id FROM departments WHERE LOWER(department_name) = LOWER(%s)",
                (department_name,),
                fetch="one"
            )
            if existing:
                errors["department_name"] = f"Department '{department_name}' already exists."
                
        if not errors:
            execute_query(
                "INSERT INTO departments (department_name) VALUES (%s)",
                (department_name,),
                commit=True
            )
            flash(f"Department '{department_name}' added successfully!", "success")
            return redirect(url_for("departments_list"))
            
    return render_template(
        "department_form.html",
        action="Create",
        department_name=department_name,
        errors=errors
    )

@departments_bp.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"], endpoint="department_edit")
def department_edit(dept_id):
    dept = execute_query(
        "SELECT department_id, department_name FROM departments WHERE department_id = %s",
        (dept_id,),
        fetch="one"
    )
    if not dept:
        flash(f"Department with ID {dept_id} not found.", "danger")
        return redirect(url_for("departments_list"))
        
    errors = {}
    department_name = dept["department_name"]
    
    if request.method == "POST":
        department_name = request.form.get("department_name", "").strip()
        
        if not department_name:
            errors["department_name"] = "Department name is required."
        elif len(department_name) < 2 or len(department_name) > 100:
            errors["department_name"] = "Department name must be between 2 and 100 characters."
        else:
            existing = execute_query(
                "SELECT department_id FROM departments WHERE LOWER(department_name) = LOWER(%s) AND department_id != %s",
                (department_name, dept_id),
                fetch="one"
            )
            if existing:
                errors["department_name"] = f"Another department named '{department_name}' already exists."
                
        if not errors:
            execute_query(
                "UPDATE departments SET department_name = %s WHERE department_id = %s",
                (department_name, dept_id),
                commit=True
            )
            flash(f"Department updated to '{department_name}' successfully!", "success")
            return redirect(url_for("departments_list"))
            
    return render_template(
        "department_form.html",
        action="Edit",
        dept_id=dept_id,
        department_name=department_name,
        errors=errors
    )

@departments_bp.route("/departments/<int:dept_id>/delete", methods=["POST"], endpoint="department_delete")
def department_delete(dept_id):
    dept = execute_query(
        "SELECT department_id, department_name FROM departments WHERE department_id = %s",
        (dept_id,),
        fetch="one"
    )
    if not dept:
        flash(f"Department with ID {dept_id} not found.", "danger")
        return redirect(url_for("departments_list"))
        
    visit_count_res = execute_query(
        "SELECT COUNT(*) AS total FROM visits WHERE department_id = %s",
        (dept_id,),
        fetch="one"
    )
    visit_count = visit_count_res["total"] if visit_count_res else 0
    
    if visit_count > 0:
        flash(
            f"Cannot delete '{dept['department_name']}' because it is currently referenced by {visit_count} visit record(s). "
            f"Please reassign or delete those visits before deleting this department.",
            "danger"
        )
        return redirect(url_for("departments_list"))
        
    execute_query("DELETE FROM departments WHERE department_id = %s", (dept_id,), commit=True)
    flash(f"Department '{dept['department_name']}' deleted successfully.", "success")
    return redirect(url_for("departments_list"))
