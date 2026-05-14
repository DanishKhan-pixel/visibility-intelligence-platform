from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.discovery_agent import QueryDiscoveryAgent
from app.agents.recommendation_agent import ContentRecommendationAgent
from app.agents.scoring_agent import VisibilityScoringAgent
from app.models.base import db
from app.models.pipeline_run import PipelineRun
from app.models.profile import BusinessProfile
from app.models.query import DiscoveredQuery
from app.models.recommendation import Recommendation


@dataclass
class PipelineResponse:
    pipeline_id: str
    status: str
    queries_discovered: int
    queries_scored: int
    top_queries: list[dict]
    recommendations: list[dict]
    tokens_used: int


class PipelineOrchestrator:
    def __init__(
        self,
        discovery: QueryDiscoveryAgent | None = None,
        scoring: VisibilityScoringAgent | None = None,
        recommendation: ContentRecommendationAgent | None = None,
        logger: logging.Logger | None = None,
    ):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.discovery = discovery or QueryDiscoveryAgent(logger=self.logger)
        self.scoring = scoring or VisibilityScoringAgent(logger=self.logger)
        self.recommendation = recommendation or ContentRecommendationAgent(logger=self.logger)

    def run_for_profile(self, profile_id: str) -> PipelineResponse:
        pipeline_id = str(uuid4())
        ctx = AgentContext(pipeline_id=pipeline_id)

        profile = db.session.get(BusinessProfile, profile_id)
        if not profile:
            raise ValueError("Profile not found")

        run = PipelineRun(id=pipeline_id, profile_id=profile_id, status="running", started_at=datetime.now(timezone.utc))
        db.session.add(run)
        db.session.commit()

        tokens_used = 0
        queries_discovered = 0
        queries_scored = 0

        try:
            discovered = self.discovery.run(
                ctx,
                domain=profile.domain,
                industry=profile.industry,
                competitors=profile.competitors,
            )
            queries_discovered = len(discovered)
            run.queries_discovered = queries_discovered
            db.session.commit()

            scored_rows: list[DiscoveredQuery] = []
            for item in discovered:
                try:
                    scored = self.scoring.run(ctx, query_text=item.query_text, domain=profile.domain)
                    dq = DiscoveredQuery(
                        profile_id=profile.id,
                        run_id=run.id,
                        query_text=scored.query_text,
                        search_volume=scored.estimated_search_volume,
                        difficulty=scored.competitive_difficulty,
                        domain_visible=scored.domain_visible,
                        visibility_position=scored.visibility_position,
                        opportunity_score=scored.opportunity_score,
                    )
                    db.session.add(dq)
                    scored_rows.append(dq)
                    queries_scored += 1
                except Exception as e:
                    self.logger.exception("[%s] scoring failed for one query: %s", pipeline_id, e)
                    continue

            run.queries_scored = queries_scored
            db.session.commit()

            # top queries
            top = sorted(scored_rows, key=lambda r: r.opportunity_score, reverse=True)[:3]
            top_queries = [
                {
                    "query_uuid": r.id,
                    "query_text": r.query_text,
                    "estimated_search_volume": r.search_volume,
                    "competitive_difficulty": r.difficulty,
                    "domain_visible": r.domain_visible,
                    "visibility_position": r.visibility_position,
                    "opportunity_score": r.opportunity_score,
                    "discovered_at": r.created_at.isoformat() + "Z",
                }
                for r in top
            ]

            # Only trigger agent 3 for not-visible among top scoring (or any high scoring)
            not_visible_queries = [r.query_text for r in scored_rows if not r.domain_visible]
            rec_items = self.recommendation.run(ctx, domain=profile.domain, queries=not_visible_queries[:10])

            rec_dicts: list[dict] = []
            for rec in rec_items:
                # attach recommendation to the best matching not-visible query if possible
                target_query_id = None
                if scored_rows:
                    nv = [r for r in scored_rows if not r.domain_visible]
                    if nv:
                        target_query_id = nv[0].id

                rr = Recommendation(
                    profile_id=profile.id,
                    query_id=target_query_id,
                    title=rec.title,
                    content_type=rec.content_type,
                    priority=rec.priority,
                )
                db.session.add(rr)
                # Ensure id/timestamps are populated before building API response payload.
                db.session.flush()
                rec_dicts.append(
                    {
                        "recommendation_uuid": rr.id,
                        "target_query_uuid": target_query_id,
                        "content_type": rr.content_type,
                        "title": rr.title,
                        "rationale": rec.rationale,
                        "target_keywords": rec.target_keywords,
                        "priority": rr.priority,
                        "created_at": rr.created_at.isoformat() + "Z" if rr.created_at else None,
                    }
                )

            run.tokens_used = tokens_used
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            db.session.commit()

            return PipelineResponse(
                pipeline_id=pipeline_id,
                status=run.status,
                queries_discovered=queries_discovered,
                queries_scored=queries_scored,
                top_queries=top_queries,
                recommendations=rec_dicts,
                tokens_used=tokens_used,
            )
        except Exception as e:
            self.logger.exception("[%s] pipeline failed: %s", pipeline_id, e)
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return PipelineResponse(
                pipeline_id=pipeline_id,
                status="failed",
                queries_discovered=queries_discovered,
                queries_scored=queries_scored,
                top_queries=[],
                recommendations=[],
                tokens_used=tokens_used,
            )


def get_queries_for_profile(
    profile_id: str,
    *,
    min_score: float | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[DiscoveredQuery], int]:
    q = select(DiscoveredQuery).where(DiscoveredQuery.profile_id == profile_id)
    if min_score is not None:
        q = q.where(DiscoveredQuery.opportunity_score >= float(min_score))
    if status == "visible":
        q = q.where(DiscoveredQuery.domain_visible.is_(True))
    elif status == "not_visible":
        q = q.where(DiscoveredQuery.domain_visible.is_(False))

    q = q.order_by(DiscoveredQuery.opportunity_score.desc())

    # total
    total = db.session.execute(q).scalars().all()
    # paginate in-memory (fine for SQLite eval scale)
    start = max(0, (page - 1) * per_page)
    end = start + per_page
    return total[start:end], len(total)

