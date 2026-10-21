"""Application Factory package for Hospital Patient Data Analysis System."""

import os
from pathlib import Path
import secrets
from datetime import datetime
from flask import Flask, session, request, abort, render_template, url_for

# Prevent OpenBLAS thread allocation issues on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import sys
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import config_by_name
from app.db import close_db, DatabaseError

def create_app(config_name=None):
    """Create, configure, and assemble Flask application with modular Blueprints."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
        
    app_dir = Path(__file__).resolve().parent
    template_folder = str(app_dir / "templates")
    static_folder = str(app_dir / "static")

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )
    
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))
    
    # Teardown database connection after request
    app.teardown_appcontext(close_db)
    
    # ==========================================
    # Endpoint Aliasing Helper (Supports both un-prefixed & prefixed url_for)
    # ==========================================
    def handle_url_build_error(error, endpoint, values):
        from flask import current_app
        from werkzeug.routing.exceptions import BuildError
        for prefix in ("analytics.", "patients.", "visits.", "departments."):
            candidate = prefix + endpoint
            if candidate in current_app.view_functions:
                try:
                    return url_for(candidate, **values)
                except BuildError:
                    pass
        raise error
        
    app.url_build_error_handlers.append(handle_url_build_error)

    def generate_csrf_token():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_hex(32)
        return session["_csrf_token"]
        
    app.jinja_env.globals["csrf_token"] = generate_csrf_token
    app.jinja_env.globals["now"] = datetime.now
    
    @app.before_request
    def check_csrf():
        if request.method == "POST":
            if app.config.get("TESTING") and not app.config.get("WTF_CSRF_ENABLED", True):
                return
            token = session.get("_csrf_token", None)
            form_token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            if not token or token != form_token:
                abort(400, description="Invalid or missing CSRF security token. Please try again.")

    # ==========================================
    # Error Handlers
    # ==========================================
    @app.errorhandler(400)
    def bad_request_error(e):
        return render_template(
            "error.html", 
            error_code=400, 
            title="Bad Request", 
            message=getattr(e, "description", "The request could not be processed.")
        ), 400

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template(
            "error.html", 
            error_code=404, 
            title="Page Not Found", 
            message="The requested page or record could not be found."
        ), 404

    @app.errorhandler(DatabaseError)
    def handle_database_error(e):
        return render_template(
            "error.html", 
            error_code=500, 
            title="Database Error", 
            message=str(e)
        ), 500

    @app.errorhandler(500)
    def internal_error(e):
        return render_template(
            "error.html", 
            error_code=500, 
            title="Internal Server Error", 
            message="An unexpected server error occurred. Please contact the administrator."
        ), 500

    # ==========================================
    # Register Modular Blueprints
    # ==========================================
    from app.routes.analytics import analytics_bp
    from app.routes.patients import patients_bp
    from app.routes.visits import visits_bp
    from app.routes.departments import departments_bp
    
    app.register_blueprint(analytics_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(visits_bp)
    app.register_blueprint(departments_bp)
    
    return app
