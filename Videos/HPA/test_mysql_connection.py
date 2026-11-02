"""Database Connection Verification Script.
Performs end-to-end verification of MySQL connection, schema existence,
read capabilities, and transactional write/cleanup.
NEVER prints sensitive credentials or passwords.
"""

import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure thread limit to prevent Windows OpenBLAS crash
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from config import Config
import pymysql
import pymysql.cursors

def mask_credential(value):
    """Mask sensitive string values."""
    if not value:
        return "[NOT SET]"
    return "********"

def run_db_verification():
    print("=" * 65)
    print("  MySQL Connection & Database Integrity Verification")
    print("=" * 65)

    # 1. Check database configuration
    print("\n[STEP 1] Checking Database Configuration & Settings:")
    print(f"  - Host:      {Config.MYSQL_HOST}")
    print(f"  - Port:      {Config.MYSQL_PORT}")
    print(f"  - User:      {Config.MYSQL_USER}")
    print(f"  - Database:  {Config.MYSQL_DB}")
    print(f"  - Password:  {mask_credential(Config.MYSQL_PASSWORD)}")
    
    if not Config.MYSQL_HOST or not Config.MYSQL_USER or not Config.MYSQL_DB:
        print("  [ERROR] Database configuration values are missing in .env.")
        sys.exit(1)
    print("  -> Configuration settings loaded successfully.")

    # 2. Run real connection test
    print("\n[STEP 2] Connecting to MySQL Server:")
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        print("  -> Connected successfully to MySQL instance.")
    except Exception as err:
        print(f"  [ERROR] Failed to connect to MySQL: {err}")
        sys.exit(1)

    try:
        with connection.cursor() as cursor:
            # Check MySQL version
            cursor.execute("SELECT VERSION() AS version, DATABASE() AS current_db;")
            info = cursor.fetchone()
            print(f"  -> MySQL Server Version: {info['version']}")
            print(f"  -> Active Database:      {info['current_db']}")

            # 3. Verify hospital_analytics database and tables exist
            print("\n[STEP 3] Verifying Database and Tables:")
            cursor.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            print(f"  -> Existing tables in '{Config.MYSQL_DB}': {tables}")

            required_tables = ["departments", "patients", "visits"]
            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                print(f"  [ERROR] Missing required table(s): {missing_tables}")
                sys.exit(1)
            print("  -> All 3 required tables (departments, patients, visits) exist.")

            # 4. Run simple SELECT queries to confirm read capability
            print("\n[STEP 4] Testing SELECT (Read Operations):")
            cursor.execute("SELECT COUNT(*) AS total_patients FROM patients;")
            p_count = cursor.fetchone()["total_patients"]

            cursor.execute("SELECT COUNT(*) AS total_departments FROM departments;")
            d_count = cursor.fetchone()["total_departments"]

            cursor.execute("SELECT COUNT(*) AS total_visits FROM visits;")
            v_count = cursor.fetchone()["total_visits"]

            print(f"  -> Total patients in database:    {p_count}")
            print(f"  -> Total departments in database: {d_count}")
            print(f"  -> Total visits in database:      {v_count}")

            # Sample row preview
            cursor.execute("SELECT department_id, department_name FROM departments ORDER BY department_id ASC LIMIT 3;")
            sample_depts = cursor.fetchall()
            print(f"  -> Sample departments read: {[d['department_name'] for d in sample_depts]}")
            print("  -> SELECT read operations confirmed working.")

            # 5. Test safe INSERT, SELECT, and DELETE of a fictional test record
            print("\n[STEP 5] Testing Safe Insert, Retrieve & Cleanup (Write Operations):")
            cursor.execute(
                "INSERT INTO patients (age_group, gender) VALUES (%s, %s);",
                ("18-35", "Other")
            )
            temp_patient_id = cursor.lastrowid
            connection.commit()
            print(f"  -> Inserted temporary test patient with generated ID: #{temp_patient_id}")

            cursor.execute(
                "SELECT patient_id, age_group, gender FROM patients WHERE patient_id = %s;",
                (temp_patient_id,)
            )
            retrieved = cursor.fetchone()
            assert retrieved is not None, "Failed to retrieve the inserted test patient."
            assert retrieved["patient_id"] == temp_patient_id
            print(f"  -> Verified test record retrieval: ID={retrieved['patient_id']}, Age Group={retrieved['age_group']}, Gender={retrieved['gender']}")

            cursor.execute("DELETE FROM patients WHERE patient_id = %s;", (temp_patient_id,))
            connection.commit()
            print(f"  -> Cleaned up and deleted temporary test patient #{temp_patient_id}.")

            cursor.execute("SELECT patient_id FROM patients WHERE patient_id = %s;", (temp_patient_id,))
            assert cursor.fetchone() is None, "Failed to delete temporary test patient."
            print("  -> Deletion verified. Database remains intact with 0 residual test data.")

        connection.close()

        print("\n" + "=" * 65)
        print("  RESULT: MySQL CONNECTION AND INTEGRITY VERIFIED 100% WORKING")
        print("=" * 65)

    except Exception as err:
        print(f"\n[ERROR] An unexpected error occurred during database testing: {err}")
        if connection and connection.open:
            connection.rollback()
            connection.close()
        sys.exit(1)

if __name__ == "__main__":
    run_db_verification()
