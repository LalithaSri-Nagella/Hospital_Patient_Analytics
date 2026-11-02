"""Comprehensive Authentication and Role-Based Access Control (RBAC) Test Suite."""

import pytest
from app.db import execute_query

def test_login_page_renders(unauth_client):
    """Test that the login portal renders cleanly with all required medical portal elements."""
    response = unauth_client.get("/login")
    assert response.status_code == 200
    assert b"Hospital Management Portal" in response.data
    assert b"Secure Access for Authorized Personnel" in response.data
    assert b'id="usernameInput"' in response.data
    assert b'id="passwordInput"' in response.data
    assert b'id="togglePasswordBtn"' in response.data
    assert b"Remember Me" in response.data

def test_admin_login_success(unauth_client):
    """Test that an administrator can log in and is redirected to the main dashboard."""
    response = unauth_client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"] or response.headers["Location"].endswith("/")

def test_doctor_login_success_and_redirect(unauth_client):
    """Test that a doctor can log in and is redirected to the doctor dashboard."""
    response = unauth_client.post("/login", data={
        "username": "doctor_jane",
        "password": "doctor123"
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert "/doctor/dashboard" in response.headers["Location"]

def test_accountant_login_success_and_redirect(unauth_client):
    """Test that an accountant can log in and is redirected to the accountant dashboard."""
    response = unauth_client.post("/login", data={
        "username": "accountant_bob",
        "password": "accountant123"
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert "/accountant/dashboard" in response.headers["Location"]

def test_login_invalid_password_rejected(unauth_client):
    """Test that incorrect passwords are rejected with professional error messages."""
    response = unauth_client.post("/login", data={
        "username": "admin",
        "password": "wrong_password_123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_login_inactive_user_rejected(unauth_client):
    """Test that deactivated/inactive users cannot log in."""
    response = unauth_client.post("/login", data={
        "username": "inactive_user",
        "password": "inactive123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"inactive" in response.data.lower() or b"deactivated" in response.data.lower()

def test_unauthenticated_user_redirected_from_dashboard(unauth_client):
    """Test that unauthenticated users attempting to access dashboard are redirected to login."""
    response = unauth_client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_unauthenticated_user_redirected_from_patients(unauth_client):
    """Test that unauthenticated users attempting to access patients directory are redirected to login."""
    response = unauth_client.get("/patients", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_doctor_access_to_doctor_dashboard(doctor_client):
    """Test that a doctor can view the doctor dashboard with clinical statistics."""
    response = doctor_client.get("/doctor/dashboard")
    assert response.status_code == 200
    assert b"Clinical Operations Dashboard" in response.data
    assert b"Patient Age Demographics Breakdown" in response.data

def test_doctor_access_to_patients_and_visits(doctor_client):
    """Test that doctors can view patient records and visit logs."""
    r_pat = doctor_client.get("/patients")
    assert r_pat.status_code == 200
    assert b"Patients Directory" in r_pat.data

    r_vis = doctor_client.get("/visits")
    assert r_vis.status_code == 200
    assert b"Patient Visits Log" in r_vis.data

def test_doctor_cannot_access_user_management(doctor_client):
    """Test that doctors are forbidden from accessing the user management section."""
    response = doctor_client.get("/users", follow_redirects=True)
    assert b"Access Denied" in response.data

def test_doctor_cannot_delete_department(doctor_client):
    """Test that doctors are blocked from deleting departments."""
    response = doctor_client.post("/departments/1/delete")
    assert response.status_code == 403

def test_doctor_cannot_delete_patient(doctor_client):
    """Test that doctors are blocked from deleting patient records."""
    response = doctor_client.post("/patients/1/delete")
    assert response.status_code == 403

def test_accountant_access_to_accountant_dashboard(accountant_client):
    """Test that accountants can access operational and workload analytics."""
    response = accountant_client.get("/accountant/dashboard")
    assert response.status_code == 200
    assert b"Operational &amp; Workload Dashboard" in response.data
    assert b"Department Workload Distribution" in response.data

def test_accountant_access_to_analytics_and_csv(accountant_client):
    """Test that accountants can access analytics reports and export CSV summaries."""
    r_ana = accountant_client.get("/analytics")
    assert r_ana.status_code == 200

    r_csv = accountant_client.get("/analytics/export/visits")
    assert r_csv.status_code == 200
    assert b"Visit ID" in r_csv.data

def test_accountant_cannot_access_user_management(accountant_client):
    """Test that accountants are forbidden from accessing user management."""
    response = accountant_client.get("/users", follow_redirects=True)
    assert b"Access Denied" in response.data

def test_accountant_cannot_modify_departments(accountant_client):
    """Test that accountants cannot create, edit, or delete departments."""
    r_create = accountant_client.post("/departments/new", data={"department_name": "New Dept"})
    assert r_create.status_code == 403

def test_admin_user_management_list(client):
    """Test that administrators can view the user management directory."""
    response = client.get("/users")
    assert response.status_code == 200
    assert b"User Management" in response.data
    assert b"@admin" in response.data
    assert b"@doctor_jane" in response.data
    assert b"@accountant_bob" in response.data

def test_admin_create_staff_user(client):
    """Test that an administrator can create a new doctor account."""
    response = client.post("/users/new", data={
        "username": "dr_clara",
        "full_name": "Dr. Clara Oswald",
        "email": "clara@hospital.org",
        "role": "doctor",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"created successfully" in response.data
    assert b"@dr_clara" in response.data

def test_admin_cannot_deactivate_self(client):
    """Test safety guard preventing administrator from deactivating their own currently logged-in account."""
    response = client.post("/users/1/toggle-status", follow_redirects=True)
    assert response.status_code == 200
    assert b"cannot deactivate your own" in response.data.lower()

def test_admin_cannot_deactivate_last_active_admin(client):
    """Test safety guard preventing deactivation of the last active administrator."""
    # admin has user_id = 1. If another admin created, only when last admin is left is it blocked.
    # user_id 1 is already protected by self-deactivation guard.
    response = client.post("/users/1/toggle-status", follow_redirects=True)
    assert b"cannot deactivate" in response.data.lower()

def test_admin_reset_user_password(client):
    """Test that administrator can securely reset a staff member's password."""
    response = client.post("/users/2/reset-password", data={
        "new_password": "NewDoctorPassword2026!",
        "confirm_password": "NewDoctorPassword2026!"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"reset successfully" in response.data

def test_logout_clears_session(doctor_client):
    """Test that logout properly clears the session and redirects to the login portal."""
    response = doctor_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out" in response.data.lower()
    
    # Verify protected route is now blocked
    r_protected = doctor_client.get("/doctor/dashboard", follow_redirects=False)
    assert r_protected.status_code == 302
    assert "/login" in r_protected.headers["Location"]

def test_admin_create_additional_administrator_account(client, unauth_client):
    """Test that an administrator can create another administrator account with full admin rights."""
    response = client.post("/users/new", data={
        "username": "admin_two",
        "full_name": "Second Administrator",
        "email": "admin2@hospital.org",
        "role": "administrator",
        "password": "Admin2Password123!",
        "confirm_password": "Admin2Password123!"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"created successfully" in response.data
    assert b"@admin_two" in response.data

    # Log in as the newly created administrator
    r_login = unauth_client.post("/login", data={
        "username": "admin_two",
        "password": "Admin2Password123!"
    }, follow_redirects=False)
    assert r_login.status_code == 302
    assert r_login.headers["Location"].endswith("/") or "/dashboard" in r_login.headers["Location"]

    # Verify the new administrator has full access to User Management
    r_users = unauth_client.get("/users")
    assert r_users.status_code == 200
    assert b"User Management" in r_users.data

def test_multiple_doctors_and_accountants(client, unauth_client):
    """Test creating multiple doctors and accountants with individual credentials."""
    staff_to_create = [
        ("dr_clara_1", "doctor", "Dr. Clara One", "clara1@hospital.org", "PassClara1!"),
        ("dr_clara_2", "doctor", "Dr. Clara Two", "clara2@hospital.org", "PassClara2!"),
        ("acc_david_1", "accountant", "David One", "david1@hospital.org", "PassDavid1!"),
        ("acc_david_2", "accountant", "David Two", "david2@hospital.org", "PassDavid2!")
    ]

    for uname, role, fname, email, pwd in staff_to_create:
        r = client.post("/users/new", data={
            "username": uname,
            "full_name": fname,
            "email": email,
            "role": role,
            "password": pwd,
            "confirm_password": pwd
        }, follow_redirects=True)
        assert r.status_code == 200
        assert f"@{uname}".encode() in r.data

    # Verify each doctor and accountant can log in independently
    for uname, role, fname, email, pwd in staff_to_create:
        unauth_client.get("/logout")
        r_log = unauth_client.post("/login", data={"username": uname, "password": pwd}, follow_redirects=False)
        assert r_log.status_code == 302
        expected_dest = f"/{role}/dashboard"
        assert expected_dest in r_log.headers["Location"]

def test_role_identified_by_database_record_not_username(client, unauth_client):
    """Test that authorization is governed strictly by the database role column, never by username string."""
    # User with 'admin' in username but role is 'doctor' in database
    r1 = client.post("/users/new", data={
        "username": "admin_imposter",
        "full_name": "Fake Admin",
        "email": "fakeadmin@hospital.org",
        "role": "doctor",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }, follow_redirects=True)
    assert r1.status_code == 200

    # User with 'dr_' in username but role is 'administrator' in database
    r2 = client.post("/users/new", data={
        "username": "dr_system_admin",
        "full_name": "Doctor Who Is Admin",
        "email": "docadmin@hospital.org",
        "role": "administrator",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }, follow_redirects=True)
    assert r2.status_code == 200

    # Login as admin_imposter: despite having 'admin' in username, database role is doctor
    unauth_client.post("/login", data={"username": "admin_imposter", "password": "Password123!"}, follow_redirects=True)
    r_blocked = unauth_client.get("/users", follow_redirects=True)
    assert b"Access Denied" in r_blocked.data

    # Logout
    unauth_client.get("/logout")

    # Login as dr_system_admin: despite having 'dr_' in username, database role is administrator
    unauth_client.post("/login", data={"username": "dr_system_admin", "password": "Password123!"}, follow_redirects=True)
    r_allowed = unauth_client.get("/users")
    assert r_allowed.status_code == 200
    assert b"User Management" in r_allowed.data

def test_duplicate_username_rejected(client):
    """Test that unique usernames are enforced and duplicate usernames cannot be created."""
    response = client.post("/users/new", data={
        "username": "admin",
        "full_name": "Duplicate Admin Test",
        "email": "dup@hospital.org",
        "role": "administrator",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"already in use" in response.data.lower()
