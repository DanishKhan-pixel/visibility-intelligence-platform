from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import db


class DiscoveredQuery(db.Model):
    __tablename__ = "discovered_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_profiles.id"), nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("pipeline_runs.id"), nullable=True)

    query_text: Mapped[str] = mapped_column(String(500), nullable=False)

    search_volume: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    domain_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visibility_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
