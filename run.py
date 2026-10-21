"""Top-level runner script for Hospital Patient Data Analysis System.
Allows running with a simple `py run.py` from the project root.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app, test_connection

if __name__ == "__main__":
    connected, msg = test_connection()
    if connected:
        print("[SUCCESS] MySQL database connection established successfully.")
    else:
        print(f"[WARNING] Database connection test failed: {msg}")
    print("Hospital Patient Analytics running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
