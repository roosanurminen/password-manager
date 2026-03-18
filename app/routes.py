from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, flash
from .models import Users, Credentials
from . import db
main = Blueprint("main", __name__)

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

@main.before_request
def refresh_session_expiry():
  session.modified = True

@main.route("/")
def index():
    if get_session_user():
        return redirect(url_for("main.vault"))
    return render_template("login.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    error = validate_vault_credentials(username, password)
    if error:
        flash(error, "error")
        return redirect(url_for("main.login"))

    user = db.session.execute(db.select(Users).filter_by(username=username)).scalar_one_or_none()

    if not user or not user.check_password(user.master_password_hash, password):
        flash("Invalid username or password. Please try again!", "error")
        return redirect(url_for("main.login"))

    session.clear()
    print("id", user.id)
    session['user_id'] = user.id
    session.permanent = True
    return redirect(url_for("main.vault"))
    

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    error = validate_vault_credentials(username, password)
    if error:
        flash(error, 'error')
        return redirect(url_for("main.register"))
    
    error = check_master_password_strength(password)
    if error:
        flash(error, 'error')
        return redirect(url_for("main.register"))

    existing_user = db.session.execute(db.select(Users).filter_by(username=username)).scalar_one_or_none()

    if existing_user:
        flash("That username is already taken", 'error')
        return redirect(url_for("main.register"))
    
    user = Users(username=username, master_password_hash=Users.set_password(password))
    db.session.add(user)
    db.session.commit()
    flash("Account created successfully", "success")
    return redirect(url_for("main.login"))


@main.route("/vault", methods=["GET"])
def vault():
    user = get_session_user()
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    credentials = db.session.execute(db.select(Credentials.id, Credentials.service, Credentials.username, Credentials.url).filter_by(user_id=user.id)).all()
    response = make_response(render_template("vault.html", user_id=user.id, credentials=credentials))

    print(credentials)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response 
    

@main.route("/vault/add", methods=["POST"])
def add_credential():
    user = get_session_user()
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    service = request.form.get("service", "")
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    url = request.form.get("url", "")
    master_password = request.form.get("master_password", "")

    if not user.check_password(user.master_password_hash, master_password):
        flash("Incorrect master password", 'error')
        return redirect(url_for("main.vault"))

    error = validate_service_credentials(service, username, password, url, master_password, user.id)
    if error:
        flash(error, 'error')
        return redirect(url_for("main.vault"))
    
    master_password_hash = db.session.execute(db.select(Users.master_password_hash).filter_by(id=user.id)).scalar_one_or_none()

    credential = Credentials(service=service, url=url, username=username, enc_password=Credentials.encrypt_password(password, master_password_hash), user_id=user.id)
    db.session.add(credential)
    db.session.commit()
    flash("Credential saved successfully", "success")
    return redirect(url_for("main.vault"))


@main.route("/vault/show", methods=["POST"])
def show_password():
    user = get_session_user()
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    master_password = request.form.get("master_password", "")
    credential_id = request.form.get("id_show", "")

    if not user.check_password(user.master_password_hash, master_password):
        flash("Incorrect master password", 'error')
        return redirect(url_for("main.vault"))

    master_password_hash = db.session.execute(db.select(Users.master_password_hash).filter_by(id=user.id)).scalar_one_or_none()
    enc_password = db.session.execute(db.select(Credentials.enc_password).filter_by(id=credential_id, user_id=user.id)).scalar_one_or_none()
    
    if not enc_password:
        flash("Credential not found", "error")
        return redirect(url_for("main.vault"))
    
    password = Credentials.decrypt_password(enc_password, master_password_hash)
    
    if not password:
        flash("Something went wrong")
        return redirect(url_for("main.vault"))
    
    flash(f"Password: {password}", "success")
    return redirect(url_for("main.vault"))

@main.route("/vault/delete", methods=["POST"])
def delete_credential():
    user = get_session_user()
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    master_password = request.form.get("master_password", "")
    credential_id = request.form.get("id_delete", "")

    if not user.check_password(user.master_password_hash, master_password):
        flash("Incorrect master password", 'error')
        return redirect(url_for("main.vault"))

    credential = db.session.execute(db.select(Credentials).filter_by(id=credential_id, user_id=user.id)).scalar_one_or_none()
    
    if not credential:
        flash("Credential not found", "error")
        return redirect(url_for("main.vault"))
    
    try:
        db.session.delete(credential)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("Something went wrong", "error")
        return redirect(url_for("main.vault"))
    
    flash("Credential deleted successfully", "success")
    return redirect(url_for("main.vault"))


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))