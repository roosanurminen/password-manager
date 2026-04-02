from flask import session
from .models import Users, Credentials
from . import db

def validate_vault_credentials(username, password):
    """Basic validation for login and registration inputs."""
    if not username or not password:
        return "All fields are required."
    if len(username) > 80:
        return "Username is too long."
    if len(password) > 128:
        return "Password is too long."
    return None

def get_session_user():
    """Return the logged-in user based on session or None if not logged in."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    
    return db.session.execute(db.select(Users).filter_by(id=user_id)).scalar_one_or_none()

def check_master_password_strength(password):
    """Check password strength rules for master password."""
    if len(password) < 12:
        return "Password must be at least 12 characters long."
    if not any(c.isupper() for c in password):
        return "Password must include at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must include at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must include at least one digit."
    if not any(c in "!@#$%&*()_-+={}[]|\:;<>,.?/" for c in password):
        return "Password must include at least one special character."
    return None

def validate_service_credentials(service, username, password, url, master_password, user_id):
    """Validate credential entry before saving."""
    if not service or not username or not password or not url or not master_password:
        return "All fields are required."
    
    if len(service) > 80:
        return "Service name is too long."
    if len(username) > 80:
        return "Username is too long."
    if len(password) > 128:
        return "Password is too long."
    if len(url) > 255:
        return "URL is too long."
    
    # Prevent duplicate entries for same user + account
    duplicate_credentials = db.session.execute(db.select(Credentials).filter_by(user_id=user_id, username=username, url=url)).scalar_one_or_none()
    if duplicate_credentials:
        return "This account already exists."
    
    return None