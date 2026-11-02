"""Dashboard and Analytics Routes Blueprint."""

from datetime import datetime
from flask import Blueprint, render_template, request, flash, Response, redirect, url_for
from app.services.analytics_service import (
    get_dashboard_data, get_analytics_report,
    export_visits_csv, export_analytics_summary_csv,
    get_doctor_dashboard_data, get_accountant_dashboard_data
)
from app.auth import login_required, roles_required, get_current_user

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/", endpoint="dashboard")
@analytics_bp.route("/dashboard", endpoint="admin_dashboard")
@login_required
def dashboard():
    """Main landing dashboard. Routes users dynamically based on their authorized role."""
    current_u = get_current_user()

    if current_u.is_doctor():
        return redirect(url_for("analytics.doctor_dashboard"))
    elif current_u.is_accountant():
        return redirect(url_for("analytics.accountant_dashboard"))

    dashboard_data = get_dashboard_data()
    return render_template(
        "dashboard.html",
        stats=dashboard_data["stats"],
        charts=dashboard_data["charts"],
        recent_visits=dashboard_data["recent_visits"]
    )

@analytics_bp.route("/doctor/dashboard", endpoint="doctor_dashboard")
@roles_required("doctor", "administrator")
def doctor_dashboard():
    """Doctor clinical dashboard displaying patient demographics and visit registries."""
    doc_data = get_doctor_dashboard_data()
    return render_template(
        "doctor_dashboard.html",
        stats=doc_data["stats"],
        charts=doc_data["charts"],
        recent_visits=doc_data["recent_visits"]
    )

@analytics_bp.route("/accountant/dashboard", endpoint="accountant_dashboard")
@roles_required("accountant", "administrator")
def accountant_dashboard():
    """Accountant operational dashboard displaying department workload volumes and trends."""
    acc_data = get_accountant_dashboard_data()
    return render_template(
        "accountant_dashboard.html",
        stats=acc_data["stats"],
        charts=acc_data["charts"],
        dept_workload=acc_data["dept_workload"]
    )

@analytics_bp.route("/analytics", endpoint="analytics_dashboard")
@roles_required("administrator", "accountant")
def analytics_dashboard():
    """Advanced hospital analytics, KPIs, and department breakdowns."""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    for d_str in [start_date, end_date]:
        if d_str:
            try:
                datetime.strptime(d_str, "%Y-%m-%d")
            except ValueError:
                flash(f"Invalid date format: {d_str}. Expected YYYY-MM-DD.", "warning")
                start_date = ""
                end_date = ""
                break

    report = get_analytics_report(
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )

    return render_template(
        "analytics.html",
        report=report,
        start_date=start_date,
        end_date=end_date
    )

@analytics_bp.route("/analytics/export/visits", endpoint="export_visits")
@roles_required("administrator", "accountant")
def export_visits():
    """Export filtered visits dataset to CSV."""
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    department_id = request.args.get("department_id", "").strip() or None
    visit_type = request.args.get("visit_type", "").strip() or None

    csv_content = export_visits_csv(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        visit_type=visit_type
    )
    filename = f"hospital_visits_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@analytics_bp.route("/analytics/export/summary", endpoint="export_summary")
@roles_required("administrator", "accountant")
def export_summary():
    """Export aggregate analytics executive summary to CSV."""
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None

    csv_content = export_analytics_summary_csv(
        start_date=start_date,
        end_date=end_date
    )
    filename = f"hospital_analytics_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
