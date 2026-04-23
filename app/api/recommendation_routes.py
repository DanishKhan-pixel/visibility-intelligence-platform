from __future__ import annotations

from flask import Blueprint

from app.api._responses import err, ok
from app.models.base import db
from app.models.profile import BusinessProfile
from app.models.recommendation import Recommendation

bp = Blueprint("recommendations", __name__, url_prefix="/api/v1")


@bp.get("/profiles/<profile_uuid>/recommendations")
def list_recommendations(profile_uuid: str):
    profile = db.session.get(BusinessProfile, profile_uuid)
    if not profile:
        return err("profile not found", "NOT_FOUND", 404)

    rows = (
        db.session.query(Recommendation)
        .filter(Recommendation.profile_id == profile.id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    data = [
        {
            "recommendation_uuid": r.id,
            "target_query_uuid": r.query_id,
            "content_type": r.content_type,
            "title": r.title,
            "rationale": "",
            "target_keywords": [],
            "priority": r.priority,
            "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]

    return ok({"items": data, "total": len(data)})

