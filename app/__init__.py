import os
from flask import Flask
from dotenv import load_dotenv

# Load environment configurations from local .env at the very beginning
load_dotenv()

from app.config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure the database instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Bind extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register models with SQLAlchemy metadata
    from app import models

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Configure Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))

    # Register custom CLI commands
    @app.cli.command("init-db")
    def init_db():
        """Create database tables from models."""
        db.create_all()
        print("Initialized the database successfully.")

    return app
