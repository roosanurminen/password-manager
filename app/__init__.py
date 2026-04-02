from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import timedelta

# SQLAlchemy instance (database connection manager)
db = SQLAlchemy()

# CSRF protection instance
csrf = CSRFProtect()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Enable CSRF protection for all forms
    csrf.init_app(app)

    # Load configuration from environment variables
    app.config["SECRET_KEY"] = environ.get("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")

    # Session expires after 30 minutes of inactivity
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

    # Initialize database connection
    db.init_app(app)

    # Register routes from routes.py
    from .routes import main
    app.register_blueprint(main)

    # Create database tables if they don't exist yet
    with app.app_context():
        db.create_all()

    return app