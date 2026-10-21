"""Patient Management Routes Blueprint."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.db import execute_query

patients_bp = Blueprint("patients", __name__)

ALLOWED_AGE_GROUPS = ["0-17", "18-35", "36-50", "51-65", "65+"]
ALLOWED_GENDERS = ["Male", "Female", "Other", "Prefer not to say"]

@patients_bp.route("/patients", endpoint="patients_list")
def patients_list():
    search = request.args.get("search", "").strip()
    age_raw = request.args.get("age_group", "").strip()
    age_filter = "65+" if age_raw in ("65", "65+", "65 ") else age_raw
    gender_filter = request.args.get("gender", "").strip()
    sort_by = request.args.get("sort_by", "patient_id")
    sort_order = request.args.get("order", "asc").lower()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 15)
    
    valid_sort_cols = {
        "patient_id": "patient_id",
        "age_group": "age_group",
        "gender": "gender",
        "created_at": "created_at"
    }
    col = valid_sort_cols.get(sort_by, "patient_id")
    direction = "DESC" if sort_order == "desc" else "ASC"
    
    conditions = []
    params = []
    
    if search:
        if search.isdigit():
            conditions.append("patient_id = %s")
            params.append(int(search))
        else:
            conditions.append("age_group LIKE %s")
            params.append(f"%{search}%")
            
    if age_filter and age_filter in ALLOWED_AGE_GROUPS:
        conditions.append("age_group = %s")
        params.append(age_filter)
        
    if gender_filter and gender_filter in ALLOWED_GENDERS:
        conditions.append("gender = %s")
        params.append(gender_filter)
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    count_sql = f"SELECT COUNT(*) AS total FROM patients {where_clause}"
    total_res = execute_query(count_sql, tuple(params), fetch="one")
    total_items = total_res["total"] if total_res else 0
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    
    offset = (page - 1) * per_page
    
    data_sql = f"""
        SELECT patient_id, age_group, gender, created_at
        FROM patients
        {where_clause}
        ORDER BY {col} {direction}
        LIMIT %s OFFSET %s
    """
    query_params = list(params) + [per_page, offset]
    patients = execute_query(data_sql, tuple(query_params), fetch="all")
    
    return render_template(
        "patients.html",
        patients=patients,
        search=search,
        age_filter=age_filter,
        gender_filter=gender_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        allowed_age_groups=ALLOWED_AGE_GROUPS,
        allowed_genders=ALLOWED_GENDERS
    )

@patients_bp.route("/patients/new", methods=["GET", "POST"], endpoint="patient_create")
def patient_create():
    errors = {}
    form_data = {"age_group": "", "gender": ""}
    
    if request.method == "POST":
        age_group = request.form.get("age_group", "").strip()
        gender = request.form.get("gender", "").strip() or None
        
        form_data["age_group"] = age_group
        form_data["gender"] = gender or ""
        
        if not age_group:
            errors["age_group"] = "Age group is required."
        elif age_group not in ALLOWED_AGE_GROUPS:
            errors["age_group"] = f"Invalid age group. Choose from {', '.join(ALLOWED_AGE_GROUPS)}."
            
        if gender and gender not in ALLOWED_GENDERS:
            errors["gender"] = f"Invalid gender. Choose from {', '.join(ALLOWED_GENDERS)}."
            
        if not errors:
            execute_query(
                "INSERT INTO patients (age_group, gender) VALUES (%s, %s)",
                (age_group, gender),
                commit=True
            )
            flash("Patient registered successfully!", "success")
            return redirect(url_for("patients_list"))
            
    return render_template(
        "patient_form.html",
        action="Create",
        form_data=form_data,
        errors=errors,
        allowed_age_groups=ALLOWED_AGE_GROUPS,
        allowed_genders=ALLOWED_GENDERS
    )

@patients_bp.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"], endpoint="patient_edit")
def patient_edit(patient_id):
    patient = execute_query(
        "SELECT patient_id, age_group, gender FROM patients WHERE patient_id = %s",
        (patient_id,),
        fetch="one"
    )
    if not patient:
        flash(f"Patient with ID {patient_id} not found.", "danger")
        return redirect(url_for("patients_list"))
        
    errors = {}
    form_data = {
        "age_group": patient["age_group"],
        "gender": patient["gender"] or ""
    }
    
    if request.method == "POST":
        age_group = request.form.get("age_group", "").strip()
        gender = request.form.get("gender", "").strip() or None
        
        form_data["age_group"] = age_group
        form_data["gender"] = gender or ""
        
        if not age_group:
            errors["age_group"] = "Age group is required."
        elif age_group not in ALLOWED_AGE_GROUPS:
            errors["age_group"] = f"Invalid age group. Choose from {', '.join(ALLOWED_AGE_GROUPS)}."
            
        if gender and gender not in ALLOWED_GENDERS:
            errors["gender"] = f"Invalid gender. Choose from {', '.join(ALLOWED_GENDERS)}."
            
        if not errors:
            execute_query(
                "UPDATE patients SET age_group = %s, gender = %s WHERE patient_id = %s",
                (age_group, gender, patient_id),
                commit=True
            )
            flash(f"Patient #{patient_id} updated successfully!", "success")
            return redirect(url_for("patients_list"))
            
    return render_template(
        "patient_form.html",
        action="Edit",
        patient_id=patient_id,
        form_data=form_data,
        errors=errors,
        allowed_age_groups=ALLOWED_AGE_GROUPS,
        allowed_genders=ALLOWED_GENDERS
    )

@patients_bp.route("/patients/<int:patient_id>/delete", methods=["POST"], endpoint="patient_delete")
def patient_delete(patient_id):
    patient = execute_query(
        "SELECT patient_id FROM patients WHERE patient_id = %s",
        (patient_id,),
        fetch="one"
    )
    if not patient:
        flash(f"Patient with ID {patient_id} not found.", "danger")
        return redirect(url_for("patients_list"))
        
    execute_query("DELETE FROM patients WHERE patient_id = %s", (patient_id,), commit=True)
    flash(f"Patient #{patient_id} and associated visits removed successfully.", "success")
    return redirect(url_for("patients_list"))
