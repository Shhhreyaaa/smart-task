import pytest
from app import create_app
from app.extensions import db
from app.models import User

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Use a temporary in-memory SQLite database for testing
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SECRET_KEY = 'test-secret-key'
        WTF_CSRF_ENABLED = False

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_app_is_testing(app):
    """Test that the app is correctly set to testing mode."""
    assert app.config['TESTING']

def test_password_hashing(app):
    """Test that passwords are hashed and checked correctly."""
    with app.app_context():
        u = User(username='testuser', email='test@example.com')
        u.set_password('mysecretpassword')
        assert not u.check_password('wrongpassword')
        assert u.check_password('mysecretpassword')

def test_login_redirect(client):
    """Test that accessing the dashboard without logging in redirects to login."""
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
