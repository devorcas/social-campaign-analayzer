from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from shared.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def _fallback_summary(analysis: dict[str, Any]) -> str:
    visual_score = analysis.get("visual", {}).get("overall_score")
    text_score = analysis.get("text", {}).get("overall_score")
    return (
        "Automated summary fallback: analysis completed. "
        f"Visual safety score={visual_score}, text safety score={text_score}."
    )


def generate_summary(analysis: dict[str, Any], transcript_text: str | None = None) -> str:
    if not ANTHROPIC_API_KEY:
        return _fallback_summary(analysis)

    prompt = (
        "You are a content safety analyst. Produce a concise human-readable summary "
        "with: (1) content meaning, (2) transcript highlights, (3) key risks/flags.\n\n"
        f"Analysis JSON:\n{json.dumps(analysis, ensure_ascii=True)}\n\n"
        f"Transcript:\n{(transcript_text or '').strip()[:5000]}"
    )
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=400,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        return _fallback_summary(analysis)

    texts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    summary = "\n".join([t.strip() for t in texts if t and t.strip()])
    return summary or _fallback_summary(analysis)
