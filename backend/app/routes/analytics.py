"""Dashboard and Analytics Routes Blueprint."""

from datetime import datetime
from flask import Blueprint, render_template, request, flash, Response
from app.services.analytics_service import (
    get_dashboard_data, get_analytics_report,
    export_visits_csv, export_analytics_summary_csv
)

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/", endpoint="dashboard")
def dashboard():
    dashboard_data = get_dashboard_data()
    return render_template(
        "dashboard.html",
        stats=dashboard_data["stats"],
        charts=dashboard_data["charts"],
        recent_visits=dashboard_data["recent_visits"]
    )

@analytics_bp.route("/analytics", endpoint="analytics_dashboard")
def analytics_dashboard():
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
def export_visits():
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
def export_summary():
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
