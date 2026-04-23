from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify

from app.config import Config
from app.models import pipeline_run, profile, query, recommendation  # noqa: F401
from app.models.base import db
from flask_migrate import Migrate


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    _configure_logging(app)
    _register_error_handlers(app)

    db.init_app(app)
    Migrate(app, db)
    with app.app_context():
        db.create_all()

    from app.api.profile_routes import bp as profile_bp
    from app.api.query_routes import bp as query_bp
    from app.api.recommendation_routes import bp as recommendation_bp

    app.register_blueprint(profile_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(recommendation_bp)

    return app


def _configure_logging(app: Flask) -> None:
    level = app.config.get("LOG_LEVEL", "INFO")
    logging.basicConfig(level=getattr(logging, level, logging.INFO))


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
