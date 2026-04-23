from __future__ import annotations

import json
import re
from typing import Any


_JSON_OBJECT_RE = re.compile(r"(\{[\s\S]*\})")
_JSON_ARRAY_RE = re.compile(r"(\[[\s\S]*\])")


def safe_json_parse(text: str) -> Any:
    """
    Best-effort JSON parser for imperfect LLM output.
    - Tries strict json.loads
    - Falls back to extracting the first JSON object/array substring
    - Returns [] on failure (interview-safe default for pipelines)
    """
    if not text:
        return []

    try:
        return json.loads(text)
    except Exception:
        pass

    # Prefer arrays first so we don't accidentally extract an object within an array.
    for regex in (_JSON_ARRAY_RE, _JSON_OBJECT_RE):
        m = regex.search(text)
        if not m:
            continue
        try:
            return json.loads(m.group(1))
        except Exception:
            continue

    return []

