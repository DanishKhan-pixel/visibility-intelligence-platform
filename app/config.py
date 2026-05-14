from __future__ import annotations

import os
from urllib.parse import quote_plus


def _build_database_url() -> str:
    """
    Priority:
    1) DATABASE_URL if explicitly provided
    2) Postgres URL from POSTGRES_* variables
    3) local SQLite fallback
    """
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    pg_db = os.getenv("POSTGRES_DB")
    if pg_db:
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        return f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

    return "sqlite:///ai_visibility.db"


class Config:
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    DATABASE_URL = _build_database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TIMEOUT_S = int(os.getenv("OPENAI_TIMEOUT_S", "30"))

    DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
    DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
    DATAFORSEO_TIMEOUT_S = int(os.getenv("DATAFORSEO_TIMEOUT_S", "30"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
