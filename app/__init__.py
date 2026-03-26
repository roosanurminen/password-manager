from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import timedelta

db = SQLAlchemy()

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    csrf.init_app(app)
    app.config["SECRET_KEY"] = environ.get("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app