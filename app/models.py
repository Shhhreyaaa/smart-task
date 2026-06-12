from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

# Association table for Many-to-Many relationship between Tasks and Tags
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class User(db.Model, UserMixin):
    """User model for storing registration details and authentication keys."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_picture = db.Column(db.String(256), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    timezone = db.Column(db.String(64), default='UTC', nullable=True)
    theme_preference = db.Column(db.String(20), default='light', nullable=True)
    
    # Metadata timestamps and state flags
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    # backref='owner' dynamically attaches an '.owner' attribute to the Task model
    # cascade='all, delete-orphan' ensures tasks are deleted if their user is deleted
    tasks = db.relationship('Task', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Generates and sets a secure password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks raw input password against stored secure hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Task(db.Model):
    """Task model for representing action items assigned to users."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending', nullable=False)
    priority = db.Column(db.String(20), default='Medium', nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    estimated_minutes = db.Column(db.Integer, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    
    # Soft Delete mechanism
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign key constraint linking to Users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Tags relationship
    tags = db.relationship('Tag', secondary=task_tags, lazy='subquery',
        backref=db.backref('tasks', lazy=True))

    # Database level check constraints to validate exact values for status and priority
    __table_args__ = (
        db.CheckConstraint(status.in_(['Pending', 'In Progress', 'Completed']), name='check_task_status'),
        db.CheckConstraint(priority.in_(['Low', 'Medium', 'High']), name='check_task_priority'),
        db.Index('ix_task_user_deleted', 'user_id', 'is_deleted'),
        db.Index('ix_task_user_status_due', 'user_id', 'status', 'due_date'),
    )

    def __repr__(self):
        return f'<Task {self.title}>'


class Tag(db.Model):
    """Tag model for classifying tasks flexibly."""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


class Activity(db.Model):
    """Audit log for system activities."""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(255), nullable=False) # e.g., 'Created Task', 'Logged in'
    entity_type = db.Column(db.String(50), nullable=True) # e.g., 'Task', 'User'
    entity_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Activity {self.action}>'


class Notification(db.Model):
    """System notifications for users."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g., 'overdue', 'due_today'
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.type}>'
