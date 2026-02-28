from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

# Configure SQL Alchemy
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config["SECRET_KEY"] = environ.get("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")

    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app