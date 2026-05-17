from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.agents.base import AgentContext, BaseAgent
from app.utils.dataforseo_client import DataForSEOClient
from app.utils.llm_client import OpenAILLMClient
from app.utils.scoring import calculate_opportunity_score


@dataclass
class ScoredQuery:
    query_text: str
    estimated_search_volume: int
    competitive_difficulty: int
    domain_visible: bool
    visibility_position: int | None
    opportunity_score: float






class VisibilityScoringAgent(BaseAgent):
    name = "visibility_scoring"

    def __init__(
        self,
        llm: OpenAILLMClient | None = None,
        dataforseo: DataForSEOClient | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.llm = llm or OpenAILLMClient()
        self.dataforseo = dataforseo or DataForSEOClient()

    def run(self, ctx: AgentContext, *, query_text: str, domain: str) -> ScoredQuery:
        # Real search volume if possible (DataForSEO), otherwise deterministic fallback.
        metrics = self.dataforseo.get_search_volume(query_text)
        volume = int(metrics.search_volume)

        # Difficulty estimate via LLM, with deterministic fallback.
        difficulty = self._estimate_difficulty(ctx, query_text=query_text, domain=domain)

        # Visibility simulation (can be replaced by real "AI answer" checks later).
        domain_visible, position = self._simulate_visibility(query_text=query_text, domain=domain)

        score = calculate_opportunity_score(volume, difficulty, domain_visible)
        self.logger.info("[%s] %s scored query (score=%.2f)", ctx.pipeline_id, self.name, score)

        return ScoredQuery(
            query_text=query_text,
            estimated_search_volume=volume,
            competitive_difficulty=difficulty,
            domain_visible=domain_visible,
            visibility_position=position,
            opportunity_score=score,
        )

    def _estimate_difficulty(self, ctx: AgentContext, *, query_text: str, domain: str) -> int:
        system = (
            "You are an SEO strategist.\n"
            "Estimate competitive difficulty on a 0-100 scale.\n"
            "Return ONLY valid JSON: {\"difficulty\": <integer 0-100>}.\n"
        )
        user = f"Query: {query_text}\nTarget domain: {domain}\nReturn the JSON now."
        parsed, _res = self.llm.chat_json(system=system, user=user)
        try:
            if isinstance(parsed, dict) and parsed.get("difficulty") is not None:
                return int(max(0, min(100, int(parsed["difficulty"]))))
        except Exception:
            pass
        return _mock_difficulty(query_text)

    def _simulate_visibility(self, *, query_text: str, domain: str) -> tuple[bool, int | None]:
        """
        Deterministic visibility simulation:
        - approx 25% visible, position 1..5 when visible.
        """
        key = f"{domain.strip().lower()}|{query_text.strip().lower()}".encode("utf-8")
        h = hashlib.sha256(key).digest()
        visible = (h[0] % 4) == 0
        if not visible:
            return False, None
        position = (h[1] % 5) + 1
        return True, int(position)


def _mock_difficulty(query_text: str) -> int:
    h = hashlib.sha256(query_text.strip().lower().encode("utf-8")).digest()
    return int(h[0] % 101)

