from __future__ import annotations

from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from app.api._responses import err, ok
from app.models.base import db
from app.models.user import User
from app.utils.auth import hash_password, check_password, validate_email, validate_password

bp = Blueprint("auth", __name__, url_prefix="/auth")

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, user_id)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user account."""
    if request.method == "GET":
        return render_template("auth/register.html")

    # Handle both JSON API and form submissions
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        name = payload.get("name", "").strip()
        api_mode = True
    else:
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        api_mode = False

    # Validation
    if not email:
        if api_mode:
            return err("Email is required", "VALIDATION_ERROR", 400)
        flash("Email is required", "error")
        return render_template("auth/register.html", error="Email is required")

    if not validate_email(email):
        if api_mode:
            return err("Invalid email format", "VALIDATION_ERROR", 400)
        return render_template("auth/register.html", error="Invalid email format")

    is_valid, pw_error = validate_password(password)
    if not is_valid:
        if api_mode:
            return err(pw_error, "VALIDATION_ERROR", 400)
        return render_template("auth/register.html", error=pw_error)

    if not name:
        if api_mode:
            return err("Name is required", "VALIDATION_ERROR", 400)
        return render_template("auth/register.html", error="Name is required")

    existing = db.session.query(User).filter(User.email == email).first()
    if existing:
        if api_mode:
            return err("Email already registered", "VALIDATION_ERROR", 400)
        return render_template("auth/register.html", error="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
    )
    db.session.add(user)
    db.session.commit()

    login_user(user)

    if api_mode:
        return ok(
            {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "message": "Registration successful",
            },
            201,
        )

    flash("Registration successful! Welcome to AI Visibility.", "success")
    return redirect(url_for("index"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login with email and password."""
    if request.method == "GET":
        return render_template("auth/login.html")

    if request.is_json:
        payload = request.get_json(silent=True) or {}
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        api_mode = True
    else:
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        api_mode = False

    if not email or not password:
        if api_mode:
            return err("Email and password are required", "VALIDATION_ERROR", 400)
        return render_template("auth/login.html", error="Email and password are required")

    user = db.session.query(User).filter(User.email == email).first()
    if not user or not check_password(user.password_hash, password):
        if api_mode:
            return err("Invalid email or password", "AUTH_ERROR", 401)
        return render_template("auth/login.html", error="Invalid email or password")

    login_user(user)

    if api_mode:
        return ok(
            {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "message": "Login successful",
            }
        )

    flash("Welcome back!", "success")
    next_page = request.args.get("next")
    return redirect(next_page or url_for("index"))


@bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/me", methods=["GET"])
def me():
    """Get current user info."""
    if not current_user.is_authenticated:
        return err("Not authenticated", "AUTH_ERROR", 401)

    return ok(
        {
            "user_id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "created_at": current_user.created_at.isoformat() + "Z" if current_user.created_at else None,
        }
    )


def init_login_manager(app):
    """Initialize Flask-Login with the app."""
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

