import os


class Config:
    """Application configuration definitions."""
    # Loaded from environment variables with fallback defaults
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-development-secret-key-12345')
    
    # Database configuration defaults to SQLite inside the app instance/ folder
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///tasks.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day
