from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Instantiate SQLAlchemy ORM
db = SQLAlchemy()

# Instantiate Flask-Login session manager
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Instantiate CSRF protection for forms validation safety
csrf = CSRFProtect()
