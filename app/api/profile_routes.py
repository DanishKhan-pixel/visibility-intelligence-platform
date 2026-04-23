from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request

from app.api._responses import err, ok
from app.models.base import db
from app.models.profile import BusinessProfile
from app.services.pipeline_orchestrator import PipelineOrchestrator

bp = Blueprint("profiles", __name__, url_prefix="/api/v1")


@bp.post("/profiles")
def create_profile():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    domain = payload.get("domain")
    industry = payload.get("industry")
    description = payload.get("description")  # stored nowhere (kept simple); can be added if needed
    competitors = payload.get("competitors") or []

    if not isinstance(name, str) or not name.strip():
        return err("name is required", "VALIDATION_ERROR", 400)
    if not isinstance(domain, str) or not domain.strip():
        return err("domain is required", "VALIDATION_ERROR", 400)
    if competitors and not isinstance(competitors, list):
        return err("competitors must be a list", "VALIDATION_ERROR", 400)

    profile = BusinessProfile(name=name.strip(), domain=domain.strip(), industry=str(industry) if industry else None)
    profile.competitors = [str(x).strip() for x in competitors if str(x).strip()]

    db.session.add(profile)
    db.session.commit()

    return ok(
        {
            "profile_uuid": profile.id,
            "name": profile.name,
            "domain": profile.domain,
            "status": "created",
            "created_at": profile.created_at.isoformat() + "Z",
            "description": description,
        },
        201,
    )


@bp.get("/profiles/<profile_uuid>")
def get_profile(profile_uuid: str):
    profile = db.session.get(BusinessProfile, profile_uuid)
    if not profile:
        return err("profile not found", "NOT_FOUND", 404)

    # summary stats (simple)
    from app.models.query import DiscoveredQuery

    rows = db.session.query(DiscoveredQuery).filter(DiscoveredQuery.profile_id == profile.id).all()
    total = len(rows)
    avg = round(sum(r.opportunity_score for r in rows) / total, 2) if total else 0.0

    return ok(
        {
            "profile_uuid": profile.id,
            "name": profile.name,
            "domain": profile.domain,
            "industry": profile.industry,
            "competitors": profile.competitors,
            "created_at": profile.created_at.isoformat() + "Z",
            "stats": {"total_queries": total, "avg_opportunity_score": avg},
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
        }
    )


@bp.post("/profiles/<profile_uuid>/run")
def run_pipeline(profile_uuid: str):
    profile = db.session.get(BusinessProfile, profile_uuid)
    if not profile:
        return err("profile not found", "NOT_FOUND", 404)

    orchestrator = PipelineOrchestrator()
    result = orchestrator.run_for_profile(profile.id)

    return ok(
        {
            "pipeline_id": result.pipeline_id,
            "status": result.status,
            "queries_discovered": result.queries_discovered,
            "queries_scored": result.queries_scored,
            "top_queries": result.top_queries,
            "recommendations": result.recommendations,
            "tokens_used": result.tokens_used,
        }
    )

