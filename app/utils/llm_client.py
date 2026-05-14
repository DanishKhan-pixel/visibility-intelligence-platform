from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from flask import current_app

from app.utils.json_parser import safe_json_parse


@dataclass
class LLMResult:
    text: str
    tokens_used: int | None = None
    raw: dict[str, Any] | None = None


class LLMClientBase:
    """Base class for LLM providers."""

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_s: int | None = None):
        cfg = current_app.config if current_app else {}
        self.api_key = api_key if api_key is not None else cfg.get("OPENAI_API_KEY") or cfg.get("GEMINI_API_KEY")
        self.model = model if model is not None else cfg.get("OPENAI_MODEL") or cfg.get("GEMINI_MODEL", "gpt-4o")
        self.timeout_s = int(timeout_s if timeout_s is not None else cfg.get("OPENAI_TIMEOUT_S") or cfg.get("GEMINI_TIMEOUT_S", 30))
        self.provider = self._detect_provider()

    def _detect_provider(self) -> str:
        cfg = current_app.config if current_app else {}
        explicit = cfg.get("LLM_PROVIDER", "").lower()
        if explicit in ("gemini", "google"):
            return "gemini"
        if explicit == "openai" or self.api_key:
            return "openai"
        return "openai"

    def chat(self, *, system: str, user: str, response_format_json: bool = False) -> LLMResult:
        if self.provider == "gemini":
            return self._chat_gemini(system=system, user=user, response_format_json=response_format_json)
        return self._chat_openai(system=system, user=user, response_format_json=response_format_json)

    def _chat_openai(self, *, system: str, user: str, response_format_json: bool = False) -> LLMResult:
        if not self.api_key:
            return self._mock(system=system, user=user)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, timeout=self.timeout_s)
            kwargs: dict[str, Any] = {}
            if response_format_json:
                kwargs["response_format"] = {"type": "json_object"}

            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                **kwargs,
            )
            text = resp.choices[0].message.content or ""
            tokens_used = None
            try:
                tokens_used = int(getattr(resp, "usage", None).total_tokens)  # type: ignore[union-attr]
            except Exception:
                tokens_used = None

            return LLMResult(text=text, tokens_used=tokens_used, raw=_safe_dump(resp))
        except Exception:
            return self._mock(system=system, user=user)

    def _chat_gemini(self, *, system: str, user: str, response_format_json: bool = False) -> LLMResult:
        if not self.api_key:
            return self._mock(system=system, user=user)

        try:
            import google.genai as genai

            client = genai.Client(api_key=self.api_key)
            model = self.model or "gemini-2.0-flash"

            contents = [
                {"role": "user", "parts": [{"text": f"System: {system}\n\nUser: {user}"}]}
            ]

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json" if response_format_json else "text/plain",
                }
            )

            text = response.text or ""
            tokens_used = None
            try:
                if hasattr(response, "usage_metadata"):
                    tokens_used = response.usage_metadata.total_token_count
            except Exception:
                pass

            return LLMResult(text=text, tokens_used=tokens_used, raw=None)
        except Exception:
            return self._mock(system=system, user=user)

    def _mock(self, *, system: str, user: str) -> LLMResult:
        seed = f"{system}\n{user}".encode("utf-8", errors="ignore")
        tokens_used = max(1, len(seed) // 20)
        time.sleep(0.05)
        return LLMResult(
            text=json.dumps({"mock": True, "note": "API key missing or call failed"}),
            tokens_used=tokens_used,
            raw=None,
        )

    def chat_json(self, *, system: str, user: str) -> tuple[Any, LLMResult]:
        res = self.chat(system=system, user=user, response_format_json=False)
        parsed = safe_json_parse(res.text)
        return parsed, res


class OpenAILLMClient(LLMClientBase):
    """Backward compatible - uses OpenAI only."""
    pass


def _safe_dump(resp: Any) -> dict[str, Any]:
    try:
        return json.loads(resp.model_dump_json())  # type: ignore[attr-defined]
    except Exception:
        try:
            return resp.model_dump()  # type: ignore[attr-defined]
        except Exception:
            return {"raw": str(resp)}