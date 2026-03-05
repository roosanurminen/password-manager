from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import time
from sqlalchemy.exc import OperationalError

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

    max_retries = 10
    for i in range(max_retries):
        try:
            with app.app_context():
                db.create_all()
            print("Database connected successfully!")
            break
        except OperationalError:
            print(f"Database not ready, retrying ({i+1}/{max_retries})...")
            time.sleep(2)
    else:
        print("Failed to connect to the database after several attempts.")

    #with app.app_context():
        #db.create_all()

    return app