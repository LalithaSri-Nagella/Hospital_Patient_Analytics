"""Hospital Patient Data Analysis System - Main Server Runner."""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path so modules import seamlessly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Prevent OpenBLAS thread allocation issues on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from app import create_app
from app.db import test_connection

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    connected, msg = test_connection()
    if connected:
        print("[SUCCESS] MySQL database connection established successfully.")
    else:
        print(f"[WARNING] Database connection test failed: {msg}")
        print("Please verify your MySQL service is running and credentials in .env are correct.")
        
    print("Hospital Patient Analytics running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
