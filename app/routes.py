from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlsplit

from app.extensions import db
from app.models import User
from app.forms import RegisterForm, LoginForm

# Create main routing blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise redirect to login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration requests."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            full_name=form.full_name.data.strip() if form.full_name.data else None,
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash("Your account has been created successfully! Please sign in.", "success")
        return redirect(url_for('main.login'))
        
    return render_template('register.html', form=form)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login authentication checking both username or email inputs."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        login_identity = form.username_or_email.data.strip()
        
        # Check database for username OR email matches
        user = User.query.filter(
            (User.username == login_identity) | 
            (User.email == login_identity.lower())
        ).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            
            # Safe redirect checks to prevent open redirect vulnerabilities
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.dashboard')
                
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page)
            
        flash("Invalid username/email or password.", "danger")
        
    return render_template('login.html', form=form)


@main_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle secure user session destruction and redirect to login."""
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Protected Dashboard landing view template (logic placeholder)."""
    return render_template('index.html')
