from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp, Optional, NumberRange

from app.models import User


class RegisterForm(FlaskForm):
    """WTForm to validate user registration inputs."""
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(),
            Length(max=100, message="Full Name must be under 100 characters.")
        ]
    )
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=4, max=64, message="Username must be between 4 and 64 characters."),
            Regexp(
                '^[a-zA-Z0-9_.]+$',
                message="Username can only contain letters, numbers, underscores, and dots."
            )
        ]
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address."),
            Length(max=120)
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, max=64, message="Password must be at least 8 characters long.")
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message="Passwords must match.")
        ]
    )
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        """Checks for whitespace and username duplication."""
        # Trim input whitespace
        username_val = username.data.strip() if username.data else ""
        if not username_val:
            raise ValidationError("Username cannot be empty or just spaces.")
            
        user = User.query.filter_by(username=username_val).first()
        if user:
            raise ValidationError("This username is already taken. Please choose another.")

    def validate_email(self, email):
        """Checks for whitespace and email duplication."""
        # Trim input whitespace and convert to lowercase for case-insensitivity
        email_val = email.data.strip().lower() if email.data else ""
        if not email_val:
            raise ValidationError("Email cannot be empty or just spaces.")
            
        user = User.query.filter_by(email=email_val).first()
        if user:
            raise ValidationError("This email address is already registered.")

    def validate_password(self, password):
        """Ensures password contains both letters and digits for strength verification."""
        p_val = password.data
        if not any(char.isdigit() for char in p_val):
            raise ValidationError("Password must contain at least one number.")
        if not any(char.isalpha() for char in p_val):
            raise ValidationError("Password must contain at least one letter.")


class LoginForm(FlaskForm):
    """WTForm to validate login credentials, supporting username or email identification."""
    username_or_email = StringField(
        'Username or Email',
        validators=[
            DataRequired(message="Please enter your username or email address.")
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="Please enter your password.")
        ]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class TaskForm(FlaskForm):
    """Form for creating and editing tasks."""
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description')
    category = StringField('Category (Legacy)', validators=[Optional(), Length(max=50)])
    tags = StringField('Tags (Comma-separated)', validators=[Optional(), Length(max=200)])
    estimated_minutes = IntegerField('Estimated Minutes', validators=[Optional(), NumberRange(min=1)])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], default='Medium')
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], default='Pending')
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Save Task')


class ProfileForm(FlaskForm):
    """Form for updating user profile information."""
    full_name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    timezone = StringField('Timezone', validators=[Optional(), Length(max=64)])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('Please use a different email address.')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password securely."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')
