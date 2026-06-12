from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlsplit

from app.extensions import db
from app.models import User, Activity
from app.forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

def log_activity(user_id, action, entity_type=None, entity_id=None):
    """Helper to log system activities."""
    activity = Activity(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id)
    db.session.add(activity)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration requests."""
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
        
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
        
        log_activity(user.id, 'Registered Account', 'User', user.id)
        db.session.commit()
        
        flash("Your account has been created successfully! Please sign in.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login authentication checking both username or email inputs."""
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        login_identity = form.username_or_email.data.strip()
        
        user = User.query.filter(
            (User.username == login_identity) | 
            (User.email == login_identity.lower())
        ).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login_at = datetime.utcnow()
            log_activity(user.id, 'Logged In', 'User', user.id)
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('core.dashboard')
                
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page)
            
        flash("Invalid username/email or password.", "danger")
        
    return render_template('login.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle secure user session destruction and redirect to login."""
    log_activity(current_user.id, 'Logged Out', 'User', current_user.id)
    db.session.commit()
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Manage user profile."""
    form = ProfileForm(original_username=current_user.username, original_email=current_user.email, obj=current_user)
    password_form = ChangePasswordForm()
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip() if form.full_name.data else None
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.bio = form.bio.data.strip() if form.bio.data else None
        current_user.timezone = form.timezone.data.strip() if form.timezone.data else 'UTC'
        
        log_activity(current_user.id, 'Updated Profile', 'User', current_user.id)
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('profile.html', form=form, password_form=password_form)


@auth_bp.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    """Handle password changes."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            log_activity(current_user.id, 'Changed Password', 'User', current_user.id)
            db.session.commit()
            flash('Your password has been changed successfully.', 'success')
        else:
            flash('Invalid current password.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
                
    return redirect(url_for('auth.profile'))
