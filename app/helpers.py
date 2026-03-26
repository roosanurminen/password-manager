from flask import session
from .models import Users, Credentials
from . import db

def validate_vault_credentials(username, password):
    if not username or not password:
        return "All fields are required"
    if len(username) > 80:
        return "Username too long"
    if len(password) > 128:
        return "Password too long"
    return None

def get_session_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.execute(db.select(Users).filter_by(id=user_id)).scalar_one_or_none()

def check_master_password_strength(password):
    if len(password) < 12:
        return "Password must be at least 12 characters"
    if not any(c.isupper() for c in password):
        return "Pass"
    if not any(c.islower() for c in password):
        return "oo"
    if not any(c.isdigit() for c in password):
        return ",,"
    if not any(c in "!@#$%&*()_-+={}[]|\:;<>,.?/" for c in password):
        return "Password must contain at least one special character"
    

def validate_service_credentials(service, username, password, url, master_password, user_id):
    if not service or not username or not password or not url or not master_password:
        return "All fields are required"
    
    duplicate_credentials = db.session.execute(db.select(Credentials).filter_by(user_id=user_id, username=username, url=url)).scalar_one_or_none()
    if duplicate_credentials:
        return "This service with this username already exists"
    
    return None