from __future__ import annotations

from flask import Blueprint, request
from flask_login import current_user, login_required

from app.api._responses import err, ok
from app.models.base import db
from app.models.profile import BusinessProfile
from app.models.query import DiscoveredQuery
from app.services.pipeline_orchestrator import get_queries_for_profile
from app.agents.base import AgentContext
from app.agents.scoring_agent import VisibilityScoringAgent

bp = Blueprint("queries", __name__, url_prefix="/api/v1")


def _get_profile_check_uuid(profile_uuid: str) -> tuple[BusinessProfile | None, str | None]:
    """Get profile and verify ownership. Returns (profile, error_message)."""
    profile = db.session.get(BusinessProfile, profile_uuid)
    if not profile:
        return None, "profile not found"
    if profile.user_id != current_user.id:
        return None, "profile not found"
    return profile, None


@bp.get("/profiles/<profile_uuid>/queries")
@login_required
def list_queries(profile_uuid: str):
    profile, error = _get_profile_check_uuid(profile_uuid)
    if error:
        return err(error, "NOT_FOUND", 404)

    min_score = request.args.get("min_score", type=float)
    status = request.args.get("status", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    per_page = max(1, min(per_page, 100))

    rows, total = get_queries_for_profile(
        profile.id, min_score=min_score, status=status, page=page, per_page=per_page
    )

    data = [
        {
            "query_uuid": r.id,
            "query_text": r.query_text,
            "estimated_search_volume": r.search_volume,
            "competitive_difficulty": r.difficulty,
            "opportunity_score": r.opportunity_score,
            "domain_visible": r.domain_visible,
            "visibility_position": r.visibility_position,
            "discovered_at": r.created_at.isoformat() + "Z",
            "run_uuid": r.run_id,
        }
        for r in rows
    ]

    return ok({"items": data, "total": total, "page": page, "per_page": per_page})


@bp.post("/queries/<query_uuid>/recheck")
@login_required
def recheck_query(query_uuid: str):
    dq = db.session.get(DiscoveredQuery, query_uuid)
    if not dq:
        return err("query not found", "NOT_FOUND", 404)

    profile = db.session.get(BusinessProfile, dq.profile_id)
    if not profile:
        return err("profile not found for query", "NOT_FOUND", 404)

    # Verify ownership
    if profile.user_id != current_user.id:
        return err("query not found", "NOT_FOUND", 404)

    agent = VisibilityScoringAgent()
    ctx = AgentContext(pipeline_id=dq.run_id or dq.id)
    scored = agent.run(ctx, query_text=dq.query_text, domain=profile.domain)

    dq.search_volume = scored.estimated_search_volume
    dq.difficulty = scored.competitive_difficulty
    dq.domain_visible = scored.domain_visible
    dq.visibility_position = scored.visibility_position
    dq.opportunity_score = scored.opportunity_score
    db.session.commit()

    return ok(
        {
            "query_uuid": dq.id,
            "query_text": dq.query_text,
            "estimated_search_volume": dq.search_volume,
            "competitive_difficulty": dq.difficulty,
            "opportunity_score": dq.opportunity_score,
            "domain_visible": dq.domain_visible,
            "visibility_position": dq.visibility_position,
            "discovered_at": dq.created_at.isoformat() + "Z",
        }
    )




    