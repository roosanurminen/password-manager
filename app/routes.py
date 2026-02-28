from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import Users
from . import db
main = Blueprint("main", __name__)

# Routes
@main.route("/")
def index():
    if "username" in session:
        return redirect(url_for("main.vault"))
    return render_template("login.html")

# Login
@main.route("/login", methods=["POST"])
def login():
    username = request.form['username']
    password = request.form['password']
    user = db.session.execute(db.select(Users).filter_by(username=username)).scalar_one_or_none()

    if user and user.check_password(user.master_password_hash, password):
        session['username'] = username
        return redirect(url_for("main.vault"))
    else:
        return render_template("login.html",  error="Invalid credentials")

# Register
@main.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@main.route("/register", methods=["POST"])
def register():
    username = request.form['username']
    password = request.form['password']
    existing_user = db.session.execute(db.select(Users).filter_by(username=username)).scalar_one_or_none()

    if existing_user:
        return render_template("register.html", error="User already exists")
    
    user = Users(username=username, master_password_hash=Users().set_password(password))
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("main.login"))

# Vault
@main.route("/vault")
def vault():
    if "username" in session:
        return render_template("vault.html", username=session['username'])
    else:
        return redirect(url_for("main.login"))
    
# Logout
@main.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("main.login"))
   