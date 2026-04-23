from __future__ import annotations

# Import models so SQLAlchemy metadata is complete for migrations/app startup.
from app.models.pipeline_run import PipelineRun  # noqa: F401
from app.models.profile import BusinessProfile  # noqa: F401
from app.models.query import DiscoveredQuery  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401

