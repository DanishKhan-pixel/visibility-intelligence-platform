from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.models import pipeline_run, profile, query, recommendation, user  # noqa: F401
from app.models.base import db
from flask_migrate import Migrate


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object or Config)

    _configure_logging(app)
    _register_error_handlers(app)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models.user import User
        return db.session.get(User, user_id)

    from app.api.profile_routes import bp as profile_bp
    from app.api.query_routes import bp as query_bp
    from app.api.recommendation_routes import bp as recommendation_bp
    from app.api.docs_routes import bp as docs_bp
    from app.api.auth_routes import bp as auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(docs_bp)

    @app.get("/")
    @login_required
    def index():
        return render_template("index.html", user=current_user)

    @app.get("/login")
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return redirect(url_for("auth.login"))

    @app.get("/register")
    def register_page():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return redirect(url_for("auth.register"))

    return app


def _configure_logging(app: Flask) -> None:
    level = app.config.get("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _register_error_handlers(app: Flask) -> None:

    @app.errorhandler(404)
    def not_found(_: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {"message": "Not found", "code": "NOT_FOUND"},
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(_: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {"message": "Internal server error", "code": "INTERNAL_ERROR"},
                }
            ),
            500,
        )

    @app.errorhandler(400)
    def bad_request(error: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {"message": str(error) or "Bad request", "code": "BAD_REQUEST"},
                }
            ),
            400,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error: SQLAlchemyError) -> tuple[Any, int]:
        app.logger.error(f"Database error: {error}")
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {"message": "Database operation failed", "code": "DB_ERROR"},
                }
            ),
            500,
        )

    @app.errorhandler(405)
    def method_not_allowed(_: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "error": {"message": "Method not allowed", "code": "METHOD_NOT_ALLOWED"},
                }
            ),
            405,
        )