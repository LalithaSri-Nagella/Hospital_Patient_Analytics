"""Pytest Test Configuration and Fixtures for Modular Application Structure."""

import os
import sys
from pathlib import Path
import pytest

# Ensure backend folder is in Python search path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Prevent OpenBLAS thread allocation issues on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from app import create_app
from app.db import get_db

@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask application instance for testing."""
    os.environ["FLASK_ENV"] = "testing"
    application = create_app("testing")
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    
    with application.app_context():
        conn = get_db()
        with conn.cursor() as cursor:
            # Create departments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    department_id INT AUTO_INCREMENT PRIMARY KEY,
                    department_name VARCHAR(100) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """)
            # Create patients
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INT AUTO_INCREMENT PRIMARY KEY,
                    age_group VARCHAR(20) NOT NULL,
                    gender VARCHAR(20) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
            """)
            # Create visits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    department_id INT NOT NULL,
                    visit_date DATE NOT NULL,
                    visit_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_test_visit_patient FOREIGN KEY (patient_id) 
                        REFERENCES patients(patient_id) ON DELETE CASCADE,
                    CONSTRAINT fk_test_visit_department FOREIGN KEY (department_id) 
                        REFERENCES departments(department_id) ON DELETE RESTRICT
                ) ENGINE=InnoDB;
            """)
            # Create users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    role ENUM('administrator', 'doctor', 'accountant') NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_test_user_username (username),
                    INDEX idx_test_user_role (role)
                ) ENGINE=InnoDB;
            """)
        conn.commit()
        
    yield application

@pytest.fixture(autouse=True)
def clean_db(app):
    """Reset and seed isolated test database before each test function."""
    from app.auth import hash_password
    with app.app_context():
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("TRUNCATE TABLE visits;")
            cursor.execute("TRUNCATE TABLE patients;")
            cursor.execute("TRUNCATE TABLE departments;")
            cursor.execute("TRUNCATE TABLE users;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            
            # Insert standard test fixtures
            cursor.execute("""
                INSERT INTO departments (department_id, department_name) VALUES 
                (1, 'Cardiology'),
                (2, 'Emergency Medicine'),
                (3, 'Pediatrics');
            """)
            cursor.execute("""
                INSERT INTO patients (patient_id, age_group, gender) VALUES 
                (1, '18-35', 'Female'),
                (2, '36-50', 'Male'),
                (3, '65+', 'Female');
            """)
            cursor.execute("""
                INSERT INTO visits (visit_id, patient_id, department_id, visit_date, visit_type) VALUES 
                (1, 1, 1, '2026-03-01', 'Outpatient'),
                (2, 2, 2, '2026-03-02', 'Emergency'),
                (3, 1, 1, '2026-03-03', 'Follow-up');
            """)

            # Seed standard test users
            admin_pwd = hash_password("admin123")
            doc_pwd = hash_password("doctor123")
            acc_pwd = hash_password("accountant123")
            inact_pwd = hash_password("inactive123")

            cursor.execute("""
                INSERT INTO users (user_id, username, password_hash, full_name, email, role, is_active) VALUES 
                (1, 'admin', %s, 'System Administrator', 'admin@hospital.local', 'administrator', 1),
                (2, 'doctor_jane', %s, 'Dr. Jane Smith', 'jane.smith@hospital.local', 'doctor', 1),
                (3, 'accountant_bob', %s, 'Bob Miller', 'bob.miller@hospital.local', 'accountant', 1),
                (4, 'inactive_user', %s, 'Inactive Staff', 'inactive@hospital.local', 'doctor', 0);
            """, (admin_pwd, doc_pwd, acc_pwd, inact_pwd))
        conn.commit()

@pytest.fixture
def client(app):
    """A test client pre-authenticated as Administrator for backward-compatible test suites."""
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["full_name"] = "System Administrator"
        sess["email"] = "admin@hospital.local"
        sess["user_role"] = "administrator"
    return test_client

@pytest.fixture
def unauth_client(app):
    """An unauthenticated test client to test security barriers."""
    return app.test_client()

@pytest.fixture
def doctor_client(app):
    """A test client authenticated as a Doctor."""
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "doctor_jane"
        sess["full_name"] = "Dr. Jane Smith"
        sess["email"] = "jane.smith@hospital.local"
        sess["user_role"] = "doctor"
    return test_client

@pytest.fixture
def accountant_client(app):
    """A test client authenticated as an Accountant."""
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "accountant_bob"
        sess["full_name"] = "Bob Miller"
        sess["email"] = "bob.miller@hospital.local"
        sess["user_role"] = "accountant"
    return test_client

@pytest.fixture
def runner(app):
    """A test CLI runner for the application."""
    return app.test_cli_runner()
