from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentContext, BaseAgent
from app.utils.llm_client import OpenAILLMClient
from app.utils.json_parser import safe_json_parse












@dataclass
class ContentRecommendationItem:
    title: str
    content_type: str
    priority: str
    rationale: str
    target_keywords: list[str]


class ContentRecommendationAgent(BaseAgent):
    name = "content_recommendation"

    def __init__(self, llm: OpenAILLMClient | None = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or OpenAILLMClient()

    def run(self, ctx: AgentContext, *, domain: str, queries: list[str]) -> list[ContentRecommendationItem]:
        if not queries:
            return []

        system = (
            "You are a content strategist focused on improving AI visibility.\n"
            "Given queries where a domain is not visible, propose 3-5 actionable content recommendations.\n"
            "Return ONLY valid JSON matching this schema:\n"
            '{ "recommendations": ['
            '{"title":"string","content_type":"blog_post|landing_page|faq","priority":"high|medium|low",'
            '"rationale":"string","target_keywords":["string"]}'
            "] }\n"
            "Do not include markdown or extra keys."
        )
        user = f"Target domain: {domain}\nQueries:\n- " + "\n- ".join(queries[:10])

        parsed, res = self.llm.chat_json(system=system, user=user)
        self.logger.info("[%s] %s completed (tokens=%s)", ctx.pipeline_id, self.name, res.tokens_used)

        obj = parsed if isinstance(parsed, dict) else safe_json_parse(res.text)
        recs: list[ContentRecommendationItem] = []
        if isinstance(obj, dict) and isinstance(obj.get("recommendations"), list):
            for it in obj["recommendations"]:
                if not isinstance(it, dict):
                    continue
                title = it.get("title")
                if not isinstance(title, str) or not title.strip():
                    continue
                recs.append(
                    ContentRecommendationItem(
                        title=title.strip(),
                        content_type=str(it.get("content_type") or "blog_post"),
                        priority=str(it.get("priority") or "medium"),
                        rationale=str(it.get("rationale") or ""),
                        target_keywords=[str(x) for x in (it.get("target_keywords") or []) if str(x).strip()],
                    )
                )

        if not recs:
            # deterministic fallback
            q = queries[0]
            recs = [
                ContentRecommendationItem(
                    title=f"Comparison guide: {domain} vs leading alternatives",
                    content_type="blog_post",
                    priority="high",
                    rationale=f"Targets high-intent comparison queries like: {q}",
                    target_keywords=["comparison", "alternatives", domain],
                ),
                ContentRecommendationItem(
                    title=f"Best practices: How to solve {q}",
                    content_type="blog_post",
                    priority="medium",
                    rationale="Covers the query directly with actionable steps and examples.",
                    target_keywords=[q, "guide", "how to"],
                ),
                ContentRecommendationItem(
                    title="FAQ page: common questions and objections",
                    content_type="faq",
                    priority="medium",
                    rationale="Improves visibility for question-style prompts with concise answers.",
                    target_keywords=["faq", "pricing", "features"],
                ),
            ]

        return recs[:5]

