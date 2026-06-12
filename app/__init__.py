import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment configurations from local .env at the very beginning
load_dotenv()

from app.config import Config
from app.extensions import db, login_manager, csrf, migrate


def create_app(config_class=Config):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure the database instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Bind extensions
    db.init_app(app)
    # render_as_batch=True is required for SQLite ALTER TABLE support
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register models with SQLAlchemy metadata
    from app import models

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.core import core_bp
    from app.blueprints.tasks import tasks_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(tasks_bp)

    # Configure Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))

    # Configure Application Logging
    if not app.debug and not app.testing:
        logs_dir = os.path.join(app.root_path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(os.path.join(logs_dir, 'smart_tasks.log'), maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Smart Tasks startup')

    # Register Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500

    # Security Headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Basic CSP allowing Bootstrap, FontAwesome, Chart.js, FullCalendar via CDNs, Google Fonts, and Spline 3D Viewer
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://unpkg.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https://prod.spline.design; "
            "connect-src 'self' https://prod.spline.design; "
            "worker-src 'self' blob:;"
        )
        response.headers['Content-Security-Policy'] = csp
        return response

    # Register custom CLI commands
    @app.cli.command("init-db")
    def init_db():
        """Create database tables from models."""
        db.create_all()
        print("Initialized the database successfully.")

    return app
