"""Database connection and query execution helper module using PyMySQL.
Provides connection lifecycle management, parameterized queries, and graceful error handling.
"""

import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pymysql
import pymysql.cursors
from flask import current_app, g
from config import Config

class DatabaseError(Exception):
    """Custom exception raised when database operations fail."""
    pass

def get_db_config():
    """Retrieve active database credentials from Flask app config or base Config."""
    if current_app:
        return {
            "host": current_app.config.get("MYSQL_HOST", "localhost"),
            "port": current_app.config.get("MYSQL_PORT", 3306),
            "user": current_app.config.get("MYSQL_USER", "root"),
            "password": current_app.config.get("MYSQL_PASSWORD", ""),
            "database": current_app.config.get("MYSQL_DB", "hospital_analytics"),
        }
    return {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "database": Config.MYSQL_DB,
    }

def get_db():
    """Get or open a MySQL connection for the current application context."""
    if "db" not in g:
        cfg = get_db_config()
        try:
            g.db = pymysql.connect(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        except pymysql.MySQLError as err:
            raise DatabaseError(f"Database connection failed: {err}") from err
    return g.db

def close_db(e=None):
    """Close the active MySQL connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None and db.open:
        db.close()

def execute_query(sql, params=None, fetch="all", commit=False):
    """
    Execute a parameterized SQL query safely.
    
    :param sql: SQL query string with %s placeholders
    :param params: Tuple or list of parameters
    :param fetch: 'all', 'one', or 'none'
    :param commit: If True, commits the transaction
    :return: List of dicts, single dict, or dict with lastrowid and rowcount
    """
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            
            if commit:
                conn.commit()
                return {
                    "lastrowid": cursor.lastrowid,
                    "rowcount": cursor.rowcount
                }
            
            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                return cursor.fetchone()
            elif fetch == "none":
                return None
            else:
                return cursor.fetchall()
    except pymysql.MySQLError as err:
        if commit:
            conn.rollback()
        raise DatabaseError(f"Query execution failed: {err}") from err

def test_connection():
    """Test connection to the configured MySQL instance."""
    cfg = get_db_config()
    try:
        conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS status")
            result = cursor.fetchone()
        conn.close()
        return True, "Database connection successful."
    except Exception as err:
        return False, str(err)
