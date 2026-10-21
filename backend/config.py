import os
from pathlib import Path
from dotenv import load_dotenv

# Try loading .env from backend/ or project root
base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / ".env")
load_dotenv(base_dir.parent / ".env")

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "hospital-analytics-default-secret-key-2026")
    
    # MySQL Database Settings
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "hospital_analytics")
    
    # Pagination Settings
    ITEMS_PER_PAGE = 15

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration with isolated test database."""
    DEBUG = False
    TESTING = True
    MYSQL_DB = os.getenv("TEST_MYSQL_DB", "hospital_analytics_test")
    WTF_CSRF_ENABLED = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
