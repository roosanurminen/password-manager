from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, flash
from .models import Users, Credentials
from . import db
from .helpers import validate_vault_credentials, get_session_user, check_master_password_strength, validate_service_credentials

main = Blueprint("main", __name__)

@main.before_request
def refresh_session_expiry():
  """Extend session lifetime on each request."""
  session.modified = True

@main.route("/", methods=["GET"])
def index():
    """Redirect logged-in users to vault, otherwise show login page."""
    if get_session_user():
        return redirect(url_for("main.vault"))
    return render_template("login.html")


# ----------------- LOGIN -----------------
@main.route("/login", methods=['GET'])
def login():
    """Render login page."""
    return render_template("login.html")

@main.route("/login", methods=["POST"])
def login_post():
    """Handle user login."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Basic validation
    error = validate_vault_credentials(username, password)
    if error:
        flash(error, "error")
        return redirect(url_for("main.login"))

    # Fetch user
    user = db.session.execute(
        db.select(Users).filter_by(username=username)
    ).scalar_one_or_none()

    # Generic error message to prevent username enumeration
    if not user or not user.check_password(user.master_password_hash, password):
        flash("Invalid username or password.", "error")
        return redirect(url_for("main.login"))

    # Prevent session fixation
    session.clear()
    session['user_id'] = user.id
    session.permanent = True

    return redirect(url_for("main.vault"))



# ----------------- REGISTER -----------------
@main.route("/register", methods=['GET'])
def register():
    """Render registration page."""
    return render_template("register.html")

@main.route("/register", methods=["POST"])
def register_post():
    """Handle new user registration."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Basic validation
    error = validate_vault_credentials(username, password)
    if error:
        flash(error, 'error')
        return redirect(url_for("main.register"))
    
    # Password strength validation
    error = check_master_password_strength(password)
    if error:
        flash(error, 'error')
        return redirect(url_for("main.register"))

    # Check if username already exists
    existing_user = db.session.execute(
        db.select(Users).filter_by(username=username)
    ).scalar_one_or_none()

    if existing_user:
        flash("Username already exists.", 'error')
        return redirect(url_for("main.register"))
    
    # Create user
    user = Users(
        username=username, 
        master_password_hash=Users.set_password(password)
    )
    db.session.add(user)
    db.session.commit()

    flash("Account created successfully. You can now log in.", "success")
    return redirect(url_for("main.login"))


# ----------------- VAULT -----------------
@main.route("/vault", methods=["GET"])
def vault():
    """Display user's stored credentials."""
    user = get_session_user()

    # Require authentication
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    # Fetch only user's own credentials
    credentials = db.session.execute(
        db.select(
            Credentials.id, 
            Credentials.service, 
            Credentials.username, 
            Credentials.url
        ).filter_by(user_id=user.id)
    ).all()

    response = make_response(render_template("vault.html", user_id=user.id, credentials=credentials))

    # Prevent caching of sensitive data
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response 

@main.route("/vault/add", methods=["POST"])
def add_credential():
    """Add a new credential for the logged-in user."""
    user = get_session_user()

    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    service = request.form.get("service", "")
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    url = request.form.get("url", "")
    master_password = request.form.get("master_password", "")

    # Verify master password before allowing action
    if not user.check_password(user.master_password_hash, master_password):
        flash("Incorrect master password.", 'error')
        return redirect(url_for("main.vault"))

    # Validate input
    error = validate_service_credentials(
        service, username, password, url, master_password, user.id
    )
    if error:
        flash(error, 'error')
        return redirect(url_for("main.vault"))
    
    # Encrypt and store credential
    credential = Credentials(
        service=service, 
        url=url, username=username, 
        enc_password=Credentials.encrypt_password(password, master_password), 
        user_id=user.id
    )
    db.session.add(credential)
    db.session.commit()

    flash("Credential saved successfully.", "success")
    return redirect(url_for("main.vault"))

@main.route("/vault/show", methods=["POST"])
def show_password():
    """Decrypt and display a stored password."""
    user = get_session_user()

    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    master_password = request.form.get("master_password", "")
    credential_id = request.form.get("id_show", "")

    # Verify master password
    if not user.check_password(user.master_password_hash, master_password):
        flash("Incorrect master password.", 'error')
        return redirect(url_for("main.vault"))

    # Fetch only user's credential
    enc_password = db.session.execute(
        db.select(Credentials.enc_password).filter_by(
            id=credential_id, 
            user_id=user.id
        )
    ).scalar_one_or_none()

    if not enc_password:
        flash("Credential not found.", "error")
        return redirect(url_for("main.vault"))
    
    # Decrypt password
    password = Credentials.decrypt_password(enc_password, master_password)
    
    if not password:
        flash("Unable to decrypt the password.", "error")
        return redirect(url_for("main.vault"))
    
    flash(f"Password: {password}", "neutral")
    return redirect(url_for("main.vault"))

@main.route("/vault/delete", methods=["POST"])
def delete_credential():
    """Delete a credential after verifying ownership and password."""
    user = get_session_user()
    
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    
    master_password = request.form.get("master_password", "")
    credential_id = request.form.get("id_delete", "")

    # Verify master password
    if not user.check_password(user.master_password_hash, master_password):
        flash("Incorrect master password.", 'error')
        return redirect(url_for("main.vault"))

    # Ensure user owns the credential
    credential = db.session.execute(
        db.select(Credentials).filter_by(
            id=credential_id, 
            user_id=user.id
        )
    ).scalar_one_or_none()
    
    if not credential:
        flash("Credential not found.", "error")
        return redirect(url_for("main.vault"))
    
    try:
        db.session.delete(credential)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Something went wrong. Please try again.", "error")
        return redirect(url_for("main.vault"))
    
    flash("Credential deleted successfully.", "success")
    return redirect(url_for("main.vault"))

# ----------------- LOGOUT -----------------
@main.route("/logout", methods=["POST"])
def logout():
    """Log out the user by clearing the session."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))