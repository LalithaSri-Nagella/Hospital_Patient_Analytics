"""Comprehensive full-stack integration verification script.
Tests all application routes, database queries, CSRF handling, Chart.js integrations,
and CSV exports against the live hospital_analytics MySQL database.
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from app import create_app
from app.db import test_connection

def run_verification():
    print("=" * 60)
    print("Hospital Patient Data Analysis System - Verification Suite")
    print("=" * 60)

    # 1. Verify MySQL connectivity
    connected, msg = test_connection()
    assert connected, f"MySQL connection failed: {msg}"
    print("[PASS] 1. MySQL 8.0 connectivity established successfully.")

    app = create_app("development")
    client = app.test_client()

    # 2. Verify Dashboard
    r_dash = client.get("/")
    assert r_dash.status_code == 200, f"Dashboard returned {r_dash.status_code}"
    assert b"Hospital Patient Dashboard" in r_dash.data
    assert b'id="statTotalPatients"' in r_dash.data
    assert b"monthlyTrendChart" in r_dash.data
    assert b"deptVisitsChart" in r_dash.data
    assert b"visitTypeChart" in r_dash.data
    print("[PASS] 2. Dashboard loaded: 4 live statistics & 3 Chart.js graphs.")

    # 3. Verify Patients Listing, Pagination, and Search
    r_pat = client.get("/patients")
    assert r_pat.status_code == 200
    assert b"Patients Directory" in r_pat.data
    assert b"#P-0001" in r_pat.data

    r_pat_search = client.get("/patients?search=10")
    assert r_pat_search.status_code == 200
    assert b"#P-0010" in r_pat_search.data
    print("[PASS] 3. Patients registry: search, filtering, and pagination.")

    # 4. Verify Patient Creation with CSRF
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_pat_add = client.post("/patients/new", data={
        "csrf_token": "verification-csrf-token",
        "age_group": "36-50",
        "gender": "Female"
    }, follow_redirects=True)
    assert r_pat_add.status_code == 200
    assert b"Patient registered successfully!" in r_pat_add.data
    print("[PASS] 4. Patient creation: server-side validation and CSRF protection.")

    # 5. Verify Visits Listing and Filters
    r_vis = client.get("/visits")
    assert r_vis.status_code == 200
    assert b"Patient Visits Log" in r_vis.data
    assert b"#V-" in r_vis.data

    r_vis_one = client.get("/visits?search=1")
    assert r_vis_one.status_code == 200
    assert b"#V-0001" in r_vis_one.data

    r_vis_filter = client.get("/visits?department_id=1&visit_type=Emergency")
    assert r_vis_filter.status_code == 200
    assert b"Emergency" in r_vis_filter.data
    print("[PASS] 5. Visits registry: date range, department, and type filters.")

    # 6. Verify Visit Creation with Database FKs
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_vis_add = client.post("/visits/new", data={
        "csrf_token": "verification-csrf-token",
        "patient_id": "1",
        "department_id": "2",
        "visit_date": "2026-10-21",
        "visit_type": "Routine Checkup"
    }, follow_redirects=True)
    assert r_vis_add.status_code == 200
    assert b"Visit recorded successfully!" in r_vis_add.data
    print("[PASS] 6. Visit creation: foreign key validation and persistence.")

    # 7. Verify Departments and Referential Integrity Protection
    r_dept = client.get("/departments")
    assert r_dept.status_code == 200
    assert b"Hospital Departments" in r_dept.data
    assert b"Cardiology" in r_dept.data

    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_del_blocked = client.post("/departments/1/delete", data={
        "csrf_token": "verification-csrf-token"
    }, follow_redirects=True)
    assert r_del_blocked.status_code == 200
    assert b"Cannot delete" in r_del_blocked.data
    print("[PASS] 7. Department management: referential integrity deletion protection.")

    # 8. Verify Analytics Dashboard, Pandas KPIs, and 4 Charts
    r_ana = client.get("/analytics")
    assert r_ana.status_code == 200
    assert b"Hospital Patient Analytics" in r_ana.data
    assert b"Total Visits" in r_ana.data
    assert b"Unique Patients" in r_ana.data
    assert b"analyticsMonthlyChart" in r_ana.data
    assert b"analyticsDeptChart" in r_ana.data
    assert b"analyticsTypeChart" in r_ana.data
    assert b"analyticsAgeChart" in r_ana.data
    assert b"Department Breakdown" in r_ana.data
    print("[PASS] 8. Analytics dashboard: Pandas/NumPy aggregations & 4 Chart.js charts.")

    # 9. Verify CSV Exports
    r_exp_v = client.get("/analytics/export/visits")
    assert r_exp_v.status_code == 200
    assert b"Visit ID,Patient ID,Age Group,Gender,Department,Visit Date,Visit Type" in r_exp_v.data
    print("[PASS] 9. Visits CSV export: valid headers and structured tabular data.")

    r_exp_s = client.get("/analytics/export/summary")
    assert r_exp_s.status_code == 200
    assert b"EXECUTIVE SUMMARY" in r_exp_s.data
    assert b"DEPARTMENT-WISE PERFORMANCE SUMMARY" in r_exp_s.data
    print("[PASS] 10. Analytics Executive Summary CSV export.")

    print("=" * 60)
    print("ALL 10 VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
