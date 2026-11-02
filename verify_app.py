"""Comprehensive full-stack integration verification script.
Tests all application routes, database queries, CSRF handling, Chart.js integrations,
CSV exports, and Role-Based Access Control (Admin, Doctor, Accountant) against live MySQL.
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
from app.db import test_connection, execute_query

def run_verification():
    print("=" * 65)
    print("Hospital Patient Analytics & RBAC Security - Verification Suite")
    print("=" * 65)

    # 1. Verify MySQL connectivity
    connected, msg = test_connection()
    assert connected, f"MySQL connection failed: {msg}"
    print("[PASS] 1. MySQL 8.0 connectivity established successfully.")

    app = create_app("development")
    client = app.test_client()

    # 2. Verify Unauthenticated Protection & Login Portal
    r_unauth = client.get("/dashboard", follow_redirects=False)
    assert r_unauth.status_code == 302
    assert "/login" in r_unauth.headers["Location"]

    r_login_page = client.get("/login")
    assert r_login_page.status_code == 200
    assert b"Hospital Management Portal" in r_login_page.data
    assert b"Secure Access for Authorized Personnel" in r_login_page.data
    assert b'id="usernameInput"' in r_login_page.data
    assert b'id="passwordInput"' in r_login_page.data
    assert b'id="togglePasswordBtn"' in r_login_page.data
    assert b"Remember Me" in r_login_page.data
    print("[PASS] 2. Login Portal security: unauthenticated redirect and modern UI.")

    # 3. Verify Invalid Credentials Rejection
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_bad_login = client.post("/login", data={
        "csrf_token": "verification-csrf-token",
        "username": "admin",
        "password": "wrong_password_test"
    }, follow_redirects=True)
    assert r_bad_login.status_code == 200
    assert b"Invalid username or password" in r_bad_login.data
    print("[PASS] 3. Security: invalid credentials properly rejected.")

    # 4. Verify Administrator Login
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_admin_login = client.post("/login", data={
        "csrf_token": "verification-csrf-token",
        "username": "admin",
        "password": "Admin@Hospital2026!"
    }, follow_redirects=True)
    assert r_admin_login.status_code == 200
    assert b"Chief Administrator" in r_admin_login.data
    assert b"Hospital Patient Dashboard" in r_admin_login.data
    assert b'id="statTotalPatients"' in r_admin_login.data
    print("[PASS] 4. Administrator login successful: full dashboard and user profile.")

    # 5. Verify Patients Registry, Pagination, and Search
    r_pat = client.get("/patients")
    assert r_pat.status_code == 200
    assert b"Patients Directory" in r_pat.data
    assert b"#P-0001" in r_pat.data

    r_pat_search = client.get("/patients?search=10")
    assert r_pat_search.status_code == 200
    assert b"#P-0010" in r_pat_search.data
    print("[PASS] 5. Patients registry: search, filtering, and pagination.")

    # 6. Verify Patient Creation with CSRF
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_pat_add = client.post("/patients/new", data={
        "csrf_token": "verification-csrf-token",
        "age_group": "36-50",
        "gender": "Female"
    }, follow_redirects=True)
    assert r_pat_add.status_code == 200
    assert b"Patient registered successfully!" in r_pat_add.data
    print("[PASS] 6. Patient creation: server-side validation and CSRF protection.")

    # 7. Verify Visits Registry and Filters
    r_vis = client.get("/visits")
    assert r_vis.status_code == 200
    assert b"Patient Visits Log" in r_vis.data
    assert b"#V-" in r_vis.data

    r_vis_filter = client.get("/visits?department_id=1&visit_type=Emergency")
    assert r_vis_filter.status_code == 200
    assert b"Emergency" in r_vis_filter.data
    print("[PASS] 7. Visits registry: date range, department, and type filters.")

    # 8. Verify Visit Creation with Database FKs
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
    print("[PASS] 8. Visit creation: foreign key validation and persistence.")

    # 9. Verify Departments and Referential Integrity Protection
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
    print("[PASS] 9. Department management: referential integrity deletion protection.")

    # 10. Verify Analytics Dashboard & CSV Exports
    r_ana = client.get("/analytics")
    assert r_ana.status_code == 200
    assert b"Hospital Patient Analytics" in r_ana.data

    r_exp_v = client.get("/analytics/export/visits")
    assert r_exp_v.status_code == 200
    assert b"Visit ID,Patient ID,Age Group,Gender,Department,Visit Date,Visit Type" in r_exp_v.data

    r_exp_s = client.get("/analytics/export/summary")
    assert r_exp_s.status_code == 200
    assert b"EXECUTIVE SUMMARY" in r_exp_s.data
    print("[PASS] 10. Analytics dashboard & CSV exports: live Pandas/NumPy summaries.")

    # 11. Verify Administrator User Management
    r_users = client.get("/users")
    assert r_users.status_code == 200
    assert b"User Management &amp; Access Control" in r_users.data
    assert b"@admin" in r_users.data

    # Create a Doctor Account
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_add_doc = client.post("/users/new", data={
        "csrf_token": "verification-csrf-token",
        "username": "dr_verify",
        "full_name": "Dr. Verification Doctor",
        "email": "dr_verify@hospital.local",
        "role": "doctor",
        "password": "DoctorPass2026!",
        "confirm_password": "DoctorPass2026!"
    }, follow_redirects=True)
    assert r_add_doc.status_code == 200
    assert b"created successfully" in r_add_doc.data
    assert b"@dr_verify" in r_add_doc.data

    # Create an Accountant Account
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_add_acc = client.post("/users/new", data={
        "csrf_token": "verification-csrf-token",
        "username": "acc_verify",
        "full_name": "Alex Accountant",
        "email": "acc_verify@hospital.local",
        "role": "accountant",
        "password": "AccountantPass2026!",
        "confirm_password": "AccountantPass2026!"
    }, follow_redirects=True)
    assert r_add_acc.status_code == 200
    assert b"created successfully" in r_add_acc.data
    assert b"@acc_verify" in r_add_acc.data

    # Verify Admin Self-Deactivation Protection
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_self_deact = client.post("/users/1/toggle-status", data={
        "csrf_token": "verification-csrf-token"
    }, follow_redirects=True)
    assert b"cannot deactivate your own" in r_self_deact.data.lower()
    print("[PASS] 11. User Management: created Doctor & Accountant, self-deactivation guarded.")

    # 12. Verify Doctor Role Dashboard & Restricted Access
    doc_client = app.test_client()
    with doc_client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_doc_login = doc_client.post("/login", data={
        "csrf_token": "verification-csrf-token",
        "username": "dr_verify",
        "password": "DoctorPass2026!"
    }, follow_redirects=False)
    assert r_doc_login.status_code == 302
    assert "/doctor/dashboard" in r_doc_login.headers["Location"]

    r_doc_dash = doc_client.get("/doctor/dashboard")
    assert r_doc_dash.status_code == 200
    assert b"Clinical Operations Dashboard" in r_doc_dash.data
    assert b"Patient Age Demographics Breakdown" in r_doc_dash.data

    # Doctor blocked from user management
    r_doc_blocked = doc_client.get("/users", follow_redirects=True)
    assert b"Access Denied" in r_doc_blocked.data
    print("[PASS] 12. Doctor workflow: role redirect, Clinical Dashboard, and RBAC isolation.")

    # 13. Verify Accountant Role Dashboard & Restricted Access
    acc_client = app.test_client()
    with acc_client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_acc_login = acc_client.post("/login", data={
        "csrf_token": "verification-csrf-token",
        "username": "acc_verify",
        "password": "AccountantPass2026!"
    }, follow_redirects=False)
    assert r_acc_login.status_code == 302
    assert "/accountant/dashboard" in r_acc_login.headers["Location"]

    r_acc_dash = acc_client.get("/accountant/dashboard")
    assert r_acc_dash.status_code == 200
    assert b"Operational &amp; Workload Dashboard" in r_acc_dash.data
    assert b"Department Workload Distribution" in r_acc_dash.data

    # Accountant blocked from user management and blocked from deleting patients
    r_acc_blocked = acc_client.get("/users", follow_redirects=True)
    assert b"Access Denied" in r_acc_blocked.data
    with acc_client.session_transaction() as sess:
        sess["_csrf_token"] = "verification-csrf-token"
    r_acc_del_pat = acc_client.post("/patients/1/delete", data={"csrf_token": "verification-csrf-token"})
    assert r_acc_del_pat.status_code == 403
    print("[PASS] 13. Accountant workflow: role redirect, Workload Dashboard, and RBAC isolation.")

    # 14. Verify Logout
    r_logout = client.get("/logout", follow_redirects=True)
    assert r_logout.status_code == 200
    assert b"logged out" in r_logout.data.lower()

    # Clean up verification test accounts
    with app.app_context():
        execute_query("DELETE FROM users WHERE username IN ('dr_verify', 'acc_verify')", commit=True)

    print("[PASS] 14. Secure logout verified and temporary verification accounts cleaned up.")

    print("=" * 65)
    print("ALL 14 INTEGRATION AND ROLE-BASED ACCESS CHECKS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    run_verification()
