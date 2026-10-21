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
        conn.commit()
        
    yield application

@pytest.fixture(autouse=True)
def clean_db(app):
    """Reset and seed isolated test database before each test function."""
    with app.app_context():
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("TRUNCATE TABLE visits;")
            cursor.execute("TRUNCATE TABLE patients;")
            cursor.execute("TRUNCATE TABLE departments;")
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
        conn.commit()

@pytest.fixture
def client(app):
    """A test client for the application."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the application."""
    return app.test_cli_runner()
