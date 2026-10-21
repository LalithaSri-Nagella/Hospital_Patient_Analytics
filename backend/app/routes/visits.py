"""Visit Management Routes Blueprint."""

from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.db import execute_query

visits_bp = Blueprint("visits", __name__)

ALLOWED_VISIT_TYPES = ["Emergency", "Inpatient", "Outpatient", "Follow-up", "Routine Checkup"]

@visits_bp.route("/visits", endpoint="visits_list")
def visits_list():
    search = request.args.get("search", "").strip()
    dept_filter = request.args.get("department_id", "", type=str).strip()
    type_filter = request.args.get("visit_type", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_by = request.args.get("sort_by", "visit_id")
    sort_order = request.args.get("order", "desc").lower()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 15)
    
    valid_sort_cols = {
        "visit_id": "v.visit_id",
        "patient_id": "v.patient_id",
        "department_name": "d.department_name",
        "visit_date": "v.visit_date",
        "visit_type": "v.visit_type"
    }
    col = valid_sort_cols.get(sort_by, "v.visit_id")
    direction = "DESC" if sort_order == "desc" else "ASC"
    
    conditions = []
    params = []
    
    if search:
        if search.isdigit():
            conditions.append("(v.visit_id = %s OR v.patient_id = %s)")
            params.extend([int(search), int(search)])
        else:
            conditions.append("d.department_name LIKE %s")
            params.append(f"%{search}%")
            
    if dept_filter and dept_filter.isdigit():
        conditions.append("v.department_id = %s")
        params.append(int(dept_filter))
        
    if type_filter and type_filter in ALLOWED_VISIT_TYPES:
        conditions.append("v.visit_type = %s")
        params.append(type_filter)
        
    if start_date:
        conditions.append("v.visit_date >= %s")
        params.append(start_date)
        
    if end_date:
        conditions.append("v.visit_date <= %s")
        params.append(end_date)
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    count_sql = f"""
        SELECT COUNT(*) AS total 
        FROM visits v 
        JOIN departments d ON v.department_id = d.department_id
        {where_clause}
    """
    total_res = execute_query(count_sql, tuple(params), fetch="one")
    total_items = total_res["total"] if total_res else 0
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    
    offset = (page - 1) * per_page
    
    data_sql = f"""
        SELECT 
            v.visit_id,
            v.patient_id,
            v.department_id,
            d.department_name,
            v.visit_date,
            v.visit_type,
            p.age_group,
            p.gender
        FROM visits v
        JOIN departments d ON v.department_id = d.department_id
        JOIN patients p ON v.patient_id = p.patient_id
        {where_clause}
        ORDER BY {col} {direction}
        LIMIT %s OFFSET %s
    """
    query_params = list(params) + [per_page, offset]
    visits = execute_query(data_sql, tuple(query_params), fetch="all")
    
    departments = execute_query("SELECT department_id, department_name FROM departments ORDER BY department_name ASC", fetch="all")
    
    return render_template(
        "visits.html",
        visits=visits,
        departments=departments,
        search=search,
        dept_filter=dept_filter,
        type_filter=type_filter,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        allowed_visit_types=ALLOWED_VISIT_TYPES
    )

@visits_bp.route("/visits/new", methods=["GET", "POST"], endpoint="visit_create")
def visit_create():
    departments = execute_query("SELECT department_id, department_name FROM departments ORDER BY department_name ASC", fetch="all")
    patients = execute_query("SELECT patient_id, age_group, gender FROM patients ORDER BY patient_id DESC LIMIT 100", fetch="all")
    
    errors = {}
    form_data = {
        "patient_id": request.args.get("patient_id", ""),
        "department_id": "",
        "visit_date": date.today().strftime("%Y-%m-%d"),
        "visit_type": ""
    }
    
    if request.method == "POST":
        patient_id_val = request.form.get("patient_id", "").strip()
        department_id_val = request.form.get("department_id", "").strip()
        visit_date_val = request.form.get("visit_date", "").strip()
        visit_type_val = request.form.get("visit_type", "").strip()
        
        form_data = {
            "patient_id": patient_id_val,
            "department_id": department_id_val,
            "visit_date": visit_date_val,
            "visit_type": visit_type_val
        }
        
        if not patient_id_val or not patient_id_val.isdigit():
            errors["patient_id"] = "A valid Patient ID is required."
        else:
            p_exists = execute_query("SELECT patient_id FROM patients WHERE patient_id = %s", (int(patient_id_val),), fetch="one")
            if not p_exists:
                errors["patient_id"] = f"Patient #{patient_id_val} does not exist in the database."
                
        if not department_id_val or not department_id_val.isdigit():
            errors["department_id"] = "A Department selection is required."
        else:
            d_exists = execute_query("SELECT department_id FROM departments WHERE department_id = %s", (int(department_id_val),), fetch="one")
            if not d_exists:
                errors["department_id"] = "Selected department does not exist."
                
        if not visit_date_val:
            errors["visit_date"] = "Visit date is required."
        else:
            try:
                datetime.strptime(visit_date_val, "%Y-%m-%d")
            except ValueError:
                errors["visit_date"] = "Invalid date format. Expected YYYY-MM-DD."
                
        if not visit_type_val or visit_type_val not in ALLOWED_VISIT_TYPES:
            errors["visit_type"] = f"Please select a valid visit type ({', '.join(ALLOWED_VISIT_TYPES)})."
            
        if not errors:
            execute_query(
                """
                INSERT INTO visits (patient_id, department_id, visit_date, visit_type)
                VALUES (%s, %s, %s, %s)
                """,
                (int(patient_id_val), int(department_id_val), visit_date_val, visit_type_val),
                commit=True
            )
            flash("Visit recorded successfully!", "success")
            return redirect(url_for("visits_list"))
            
    return render_template(
        "visit_form.html",
        action="Create",
        form_data=form_data,
        errors=errors,
        departments=departments,
        patients=patients,
        allowed_visit_types=ALLOWED_VISIT_TYPES
    )

@visits_bp.route("/visits/<int:visit_id>/edit", methods=["GET", "POST"], endpoint="visit_edit")
def visit_edit(visit_id):
    visit = execute_query(
        "SELECT visit_id, patient_id, department_id, visit_date, visit_type FROM visits WHERE visit_id = %s",
        (visit_id,),
        fetch="one"
    )
    if not visit:
        flash(f"Visit with ID {visit_id} not found.", "danger")
        return redirect(url_for("visits_list"))
        
    departments = execute_query("SELECT department_id, department_name FROM departments ORDER BY department_name ASC", fetch="all")
    patients = execute_query("SELECT patient_id, age_group, gender FROM patients ORDER BY patient_id DESC LIMIT 100", fetch="all")
    
    errors = {}
    form_data = {
        "patient_id": str(visit["patient_id"]),
        "department_id": str(visit["department_id"]),
        "visit_date": visit["visit_date"].strftime("%Y-%m-%d") if isinstance(visit["visit_date"], (date, datetime)) else str(visit["visit_date"]),
        "visit_type": visit["visit_type"]
    }
    
    if request.method == "POST":
        patient_id_val = request.form.get("patient_id", "").strip()
        department_id_val = request.form.get("department_id", "").strip()
        visit_date_val = request.form.get("visit_date", "").strip()
        visit_type_val = request.form.get("visit_type", "").strip()
        
        form_data = {
            "patient_id": patient_id_val,
            "department_id": department_id_val,
            "visit_date": visit_date_val,
            "visit_type": visit_type_val
        }
        
        if not patient_id_val or not patient_id_val.isdigit():
            errors["patient_id"] = "A valid Patient ID is required."
        else:
            p_exists = execute_query("SELECT patient_id FROM patients WHERE patient_id = %s", (int(patient_id_val),), fetch="one")
            if not p_exists:
                errors["patient_id"] = f"Patient #{patient_id_val} does not exist in the database."
                
        if not department_id_val or not department_id_val.isdigit():
            errors["department_id"] = "A Department selection is required."
        else:
            d_exists = execute_query("SELECT department_id FROM departments WHERE department_id = %s", (int(department_id_val),), fetch="one")
            if not d_exists:
                errors["department_id"] = "Selected department does not exist."
                
        if not visit_date_val:
            errors["visit_date"] = "Visit date is required."
        else:
            try:
                datetime.strptime(visit_date_val, "%Y-%m-%d")
            except ValueError:
                errors["visit_date"] = "Invalid date format. Expected YYYY-MM-DD."
                
        if not visit_type_val or visit_type_val not in ALLOWED_VISIT_TYPES:
            errors["visit_type"] = f"Please select a valid visit type ({', '.join(ALLOWED_VISIT_TYPES)})."
            
        if not errors:
            execute_query(
                """
                UPDATE visits 
                SET patient_id = %s, department_id = %s, visit_date = %s, visit_type = %s
                WHERE visit_id = %s
                """,
                (int(patient_id_val), int(department_id_val), visit_date_val, visit_type_val, visit_id),
                commit=True
            )
            flash(f"Visit #{visit_id} updated successfully!", "success")
            return redirect(url_for("visits_list"))
            
    return render_template(
        "visit_form.html",
        action="Edit",
        visit_id=visit_id,
        form_data=form_data,
        errors=errors,
        departments=departments,
        patients=patients,
        allowed_visit_types=ALLOWED_VISIT_TYPES
    )

@visits_bp.route("/visits/<int:visit_id>/delete", methods=["POST"], endpoint="visit_delete")
def visit_delete(visit_id):
    visit = execute_query("SELECT visit_id FROM visits WHERE visit_id = %s", (visit_id,), fetch="one")
    if not visit:
        flash(f"Visit with ID {visit_id} not found.", "danger")
        return redirect(url_for("visits_list"))
        
    execute_query("DELETE FROM visits WHERE visit_id = %s", (visit_id,), commit=True)
    flash(f"Visit #{visit_id} deleted successfully.", "success")
    return redirect(url_for("visits_list"))
