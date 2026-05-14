import sys
from pathlib import Path

import pytest

# Ensure project root is importable when pytest is run directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.config import TestConfig
from app.models.base import db
from app.models.user import User
from app.utils.auth import hash_password


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def authenticated_client(client, app):
    """Create a test user and log them in."""
    with app.app_context():
        user = User(
            email="test@example.com",
            password_hash=hash_password("password123"),
            name="Test User"
        )
        db.session.add(user)
        db.session.commit()

    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    return client


def test_create_profile_and_run_pipeline(authenticated_client):
    resp = authenticated_client.post(
        "/api/v1/profiles",
        json={
            "name": "Acme",
            "domain": "acme.com",
            "industry": "Widgets",
            "competitors": ["example.com"],
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    profile_uuid = body["data"]["profile_uuid"]

    run = authenticated_client.post(f"/api/v1/profiles/{profile_uuid}/run")
    assert run.status_code == 200
    run_body = run.get_json()
    assert run_body["success"] is True
    assert run_body["data"]["pipeline_id"]

    q = authenticated_client.get(f"/api/v1/profiles/{profile_uuid}/queries")
    assert q.status_code == 200
    q_body = q.get_json()
    assert q_body["success"] is True
    assert q_body["data"]["total"] >= 1